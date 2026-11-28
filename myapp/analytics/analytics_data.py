import json
import random
import altair as alt
import pandas as pd
import ipaddress
import uuid
import httpx
from collections import Counter
from dataclasses import dataclass, asdict
from datetime import datetime
from statistics import mean
from typing import List, Optional

import httpagentparser

SESSION_TIMEOUT = 30 * 60  # 30 minutes in seconds

DWELL_BUCKETS = [(0, 10, "< 10 s"), (10, 30, "10-30 s"), (30, 60, "30-60 s"), (60, 180, "1-3 min"), (180, float("inf"), "> 3 min")]

@dataclass
class Session:
    session_id: str
    visitor_id: str
    start: datetime
    last_seen: datetime
    ip: str
    user_agent: str
    browser: str
    os: str
    device: str
    country: Optional[str] = None
    city: Optional[str] = None
    n_requests: int = 0

@dataclass
class Request:
    request_id: int
    session_id: str
    ts: datetime
    method: str
    path: str
    args: str
    status: int
    duration_ms: float
    referer: Optional[str]

@dataclass
class Query:
    search_id: int
    session_id: str
    ts: datetime
    text: str
    n_words: int
    method: Optional[str]
    order_in_session: int
    terms: List[str] = None
    n_results: Optional[int] = None
    mission_id: Optional[int] = None

@dataclass
class Click:
    click_id: int
    session_id: str
    ts: datetime
    pid: str
    kind: str
    search_id: Optional[int]
    rank: Optional[int]
    dwell_s: Optional[float] = None

def device_type(user_agent, agent):
    """
    httpagentparser gives browser and OS but not the kind of device, so we read it from the user agent.
    Mobile user agents contain "Mobi"; Android tablets contain "Android" but not "Mobi".
    """
    ua = user_agent.lower()
    if agent.get("bot") or "bot" in ua or "spider" in ua:
        return "Bot"
    if "ipad" in ua or "tablet" in ua or ("android" in ua and "mobi" not in ua):
        return "Tablet"
    if "mobi" in ua or "iphone" in ua:
        return "Mobile"
    return "Desktop"

# Helper functions, we return "-" if there are no values to avoid returing an error
def _avg(values):
    return round(mean(values), 1) if values else "-"

def _pct(part, total):
    return f"{100 * part / total:.0f}%" if total else "-"

def _lists(items):
    return [[str(k) for k, _ in items], [v for _, v in items]]


class AnalyticsData:
    """
    An in memory persistence object.
    Declare more variables to hold analytics tables.
    """
    # Example of statistics table
    # fact_clicks is a dictionary with the click counters: key = doc id | value = click counter
    fact_clicks = dict([])

    ### Please add your custom tables here:

    def __init__(self, geoip=False):
        self.started = datetime.now()
        self.sessions = {} # session_id -> Session
        self.requests = []
        self.queries = {} # search_id -> Query
        self.clicks = {} # click_id -> Click
        self.geoip = geoip # country / city lookup
        self._geo_cache = {} # ip -> (country, city), so we only need to lookup each IP once

    def get_session(self, session_id, visitor_id, ip, user_agent):
        """
        Called on every request
        Returns id of the active physical session of the user, opens a new one if none exists or last requests was 30 min ago
        Browser, OS, device, location are computed once per sessoin
        """
        now = datetime.now()
        s = self.sessions.get(session_id)
        # Create session if necessary
        if s is None or (now - s.last_seen).total_seconds() > SESSION_TIMEOUT:
            agent = httpagentparser.detect(user_agent or "")
            country, city = self._geo(ip)
            s = Session(uuid.uuid4().hex, visitor_id, now, now, ip, user_agent or "", agent.get("browser", {}).get("name", "Other"), agent.get("os", {}).get("name", "Other"), device_type(user_agent or "", agent), country, city)
            self.sessions[s.session_id] = s
        s.last_seen = now
        return s.session_id

    def save_request(self, session_id, method, path, args, status, duration_ms, referrer):
        """
        Stores one HTTP request
        """
        self.requests.append(Request(len(self.requests) + 1, session_id, datetime.now(), method, path, args, status, round(duration_ms, 1), referrer))

        if session_id in self.sessions:
            self.sessions[session_id].n_requests += 1

    def save_query_terms(self, terms: str, session_id = None, method = None) -> int:
        """
        old: 
            print(self)
            return random.randint(0, 100000)

        Instead of returning random number we return a real id that can be related to a real query
        """
        order = 1 + sum(q.session_id == session_id for q in self.queries.values())
        search_id = len(self.queries) + 1

        self.queries[search_id] = Query(search_id, session_id, datetime.now(), terms, len(terms.split()), method, order)

        return search_id

    def is_session_query(self, search_id, session_id):
        """
        True if the search exists and belogns to this session
        """
        q = self.queries.get(search_id)
        return q is not None and q.session_id == session_id

    def update_query_results(self, search_id, method, terms, n_results):
        """
        Called after the search
        """
        q = self.queries.get(search_id)
        if q is None or q.n_results is not None: 
            return
        q.method = method
        q.terms = list(terms)
        q.n_results = n_results
        # mission: if query shares at least one processed term with previous query, user is refining search
        # if not, start a new goal
        # mission id is search id of first query
        previous = [p for p in self.queries.values() if p.session_id == q.session_id and p.search_id < search_id]
        if previous and set(previous[-1].terms or []) & set(q.terms):
            q.mission_id = previous[-1].mission_id or previous[-1].search_id
        else:
            q.mission_id = search_id

    def save_click(self, session_id, pid, search_id = None, rank = None, kind = "result"):
        """
        Stores a click, returns its id so details page can send dwell time
        """
        if search_id not in self.queries: # direct, old or invented link
            search_id = None
            rank = None
        click_id = len(self.clicks) + 1
        self.clicks[click_id] = Click(click_id, session_id, datetime.now(), pid, kind, search_id, rank)
        return click_id

    def save_dwell(self, click_id, seconds):
        """
        Only once per click and absurd values (negative, extremely long) are ignored
        """
        c = self.clicks.get(click_id)
        if c is not None and c.kind == "result" and c.dwell_s is None and 0 <= seconds < 3 * 3600:
            c.dwell_s = round(seconds, 1)

    def _geo(self, ip):
        """
        Country and city of an IP, only for public IPs. 
        If we get an error we return no location, so we dont break the app
        """

        if not self.geoip or not ip:
            return None, None
        # if its in cache we will return that, if not we will put it in cache
        if ip not in self._geo_cache:
            self._geo_cache[ip] = (None, None)

            try:
                if ipaddress.ip_address(ip).is_global:
                    r = httpx.get(f"http://ip-api.com/json/{ip}?fields=status,country,city", timeout=2).json()
                    if r.get("status") == "success":
                        self._geo_cache[ip] = (r.get("country"), r.get("city"))
            except Exception as e:
                print("Geo lookup failed:", e)
        return self._geo_cache[ip]

    def export(self):
        """
        All tables as dicts
        """
        return {
            "sessions": [asdict(s) for s in self.sessions.values()],
            "requests": [asdict(r) for r in self.requests],
            "queries": [asdict(q) for q in self.queries.values()],
            "clicks": [asdict(c) for c in self.clicks.values()]
        }

    def dashboard_data(self, corpus, method_names):
        """
        Computes evert KPI, chart, table of the dashboard
        """
        sessions = list(self.sessions.values())
        queries = list(self.queries.values())
        done = [q for q in queries if q.n_results is not None]
        with_results = [q for q in done if q.n_results > 0]
        clicks = [c for c in self.clicks.values() if c.kind == "result"]
        outbound = [c for c in self.clicks.values() if c.kind == "outbound"]
        clicked_searches = {c.search_id for c in clicks if c.search_id is not None}
        ranks = [c.rank for c in clicks if c.rank]
        dwell = [c.dwell_s for c in clicks if c.dwell_s is not None]
        missions = Counter(q.mission_id for q in done)

        # key indicators
        kpis = {
            "Visitors": len({s.visitor_id for s in sessions}),
            "Sessions": len(sessions),
            "HTTP requests": len(self.requests),
            "Avg. response time (ms)": _avg([r.duration_ms for r in self.requests]),
            "Searches": len(queries),
            "Searches per session": round(len(queries) / len(sessions), 2) if sessions else "-",
            "Avg. words per query": _avg([q.n_words for q in queries]),
            "Zero-result searches": _pct(len(done) - len(with_results), len(done)),
            "Click-through rate": _pct(len(clicked_searches & {q.search_id for q in with_results}), len(with_results)),
            "Avg. rank of clicked results": _avg(ranks),
            "Clicks in top 3": _pct(sum(r <= 3 for r in ranks), len(ranks)),
            "Avg. dwell time (s)": _avg(dwell),
            "Outbound clicks": len(outbound),
            "Missions": len(missions),
            "Queries per mission": _avg(list(missions.values())),
        }

        hours = Counter(q.ts.hour for q in queries)
        rank_counts = Counter(min(r, 21) for r in ranks) # we group ranks after 20 as 21+
        charts = {
            "hours": [[f"{h:02d}h" for h in range(24)], [hours[h] for h in range(24)]],
            "days": _lists(sorted(Counter(r.ts.strftime("%Y-%m-%d") for r in self.requests).items())),
            "pages": _lists(Counter(r.path for r in self.requests).most_common(10)),
            "browsers": _lists(Counter(s.browser for s in sessions).most_common()),
            "os": _lists(Counter(s.os for s in sessions).most_common()),
            "devices": _lists(Counter(s.device for s in sessions).most_common()),
            "countries": _lists(Counter(s.country for s in sessions if s.country).most_common(10)),
            "top_queries": _lists(Counter(q.text.lower() for q in queries).most_common(10)),
            "top_terms": _lists(Counter(t for q in done for t in q.terms).most_common(15)),
            "query_length": _lists(sorted(Counter(q.n_words for q in queries).items())),
            "click_ranks": [[str(r) for r in range(1, 21)] + ["21+"], [rank_counts[r] for r in range(1, 22)]],
            "dwell": [[b[2] for b in DWELL_BUCKETS],
                      [sum(lo <= d < hi for d in dwell) for lo, hi, _ in DWELL_BUCKETS]],
        }

        # compare different seach methods
        methods = []
        for m in sorted({q.method for q in with_results if q.method}):
            ids = {q.search_id for q in with_results if q.method == m}
            m_ranks = [c.rank for c in clicks if c.search_id in ids and c.rank]
            methods.append({"method": method_names.get(m, m), "searches": len(ids),
                            "ctr": _pct(len(ids & clicked_searches), len(ids)), "avg_rank": _avg(m_ranks)})

        # most clicked products, position they had, how long users looked at them
        top_docs = []
        for pid, n in Counter(c.pid for c in clicks).most_common(10):
            cs = [c for c in clicks if c.pid == pid]
            top_docs.append({"pid": pid, "title": corpus[pid].title if pid in corpus else pid, "clicks": n,
                             "avg_rank": _avg([c.rank for c in cs if c.rank]),
                             "avg_dwell": _avg([c.dwell_s for c in cs if c.dwell_s is not None])})

        # last 10 sessions with their queries
        recent = []
        for s in sorted(sessions, key=lambda s: s.start, reverse=True)[:10]:
            groups = {}
            for q in queries:
                if q.session_id == s.session_id:
                    groups.setdefault(q.mission_id or q.search_id, []).append(q.text)
            recent.append({"start": s.start.strftime("%d %b %H:%M"),
                           "minutes": round((s.last_seen - s.start).total_seconds() / 60, 1),
                           "agent": f"{s.browser} · {s.os} · {s.device}",
                           "location": ", ".join(x for x in (s.city, s.country) if x) or "-",
                           "requests": s.n_requests, "missions": list(groups.values())})

        return {"since": self.started.strftime("%d %b %Y %H:%M"), "kpis": kpis, "charts": charts,
                "methods": methods, "top_docs": top_docs, "recent_sessions": recent,
                # queries that found nothing: products users want that we do not have, or unknown words
                "zero_queries": Counter(q.text.lower() for q in done if q.n_results == 0).most_common(10)}
    
    def plot_number_of_views(self):
        # Prepare data
        data = [{'Document ID': doc_id, 'Number of Views': count} for doc_id, count in self.fact_clicks.items()]
        df = pd.DataFrame(data)
        # Create Altair chart
        chart = alt.Chart(df).mark_bar().encode(
            x='Document ID',
            y='Number of Views'
        ).properties(
            title='Number of Views per Document'
        )
        # Render the chart to HTML
        return chart.to_html()


class ClickedDoc:
    def __init__(self, doc_id, description, counter):
        self.doc_id = doc_id
        self.description = description
        self.counter = counter

    def to_json(self):
        return self.__dict__

    def __str__(self):
        """
        Print the object content as a JSON string
        """
        return json.dumps(self)

import math
import os
import time
import uuid
from json import JSONEncoder

import httpagentparser  # for getting the user agent as json

from flask import Flask, abort, redirect, render_template, session, url_for, g, jsonify
from flask import request

from myapp.analytics.analytics_data import AnalyticsData, ClickedDoc
from myapp.search.load_corpus import load_corpus
from myapp.search.objects import Document, StatsDocument
from myapp.search.search_engine import SearchEngine, METHODS, DEFAULT_METHOD
from myapp.generation.constraints import parse_constraints
from myapp.generation.rag import BaselineRAGGenerator, RAGGenerator
from dotenv import load_dotenv
load_dotenv()  # take environment variables from .env


# *** for using method to_json in objects ***
def _default(self, obj):
    return getattr(obj.__class__, "to_json", _default.default)(obj)
_default.default = JSONEncoder().default
JSONEncoder.default = _default
# end lines ***for using method to_json in objects ***

#results shown per page, and how many products are sent to the LLM summary (with all their data)
RESULTS_PER_PAGE = 20
RAG_TOP_N = 10
#"improved" (default) or "baseline" (the template RAG, to compare them in the report)
RAG_MODE = os.getenv("RAG_MODE", "improved").lower()

# instantiate the Flask application
app = Flask(__name__)

# random 'secret_key' is used for persisting data in secure cookie (a new random one if .env has none)
app.secret_key = os.getenv("SECRET_KEY") or os.urandom(24)
# open browser dev tool to see the cookies
app.config["SESSION_COOKIE_NAME"] = os.getenv("SESSION_COOKIE_NAME", "irwa_session")

# paths of the data, relative to this file
path = os.path.dirname(os.path.realpath(__file__))
file_path = os.path.join(path, os.getenv("DATA_FILE_PATH", "data/fashion_products_dataset.json"))
processed_path = os.path.join(path, os.getenv("PROCESSED_CORPUS_PATH", "data/processed_corpus.pkl"))

# load documents corpus into memory (pid -> Document, with all the original fields for displaying).
corpus = load_corpus(file_path)
print(f"\nCorpus is loaded: {len(corpus):,} products")
# instantiate our search engine (index and ranking data of Parts 2-3, built once at start)
search_engine = SearchEngine(processed_path, file_path)
# instantiate our in memory persistence, GEOIP off by default as it sends visitors IPs to external service
analytics_data = AnalyticsData(geoip=os.getenv("GEOIP", "0") == "1")
# instantiate RAG generator (the improved one reads product details and category from the corpus)
rag_generator = BaselineRAGGenerator() if RAG_MODE == "baseline" else RAGGenerator(corpus, top_n=RAG_TOP_N)
print(f"RAG mode: {RAG_MODE}")

# CSS, images and the favicon are files of the pages, not user actions: they are not tracked
NOT_TRACKED = ("/static/", "/favicon.ico")
# cookie that lasts one year: the same browser is recognised across sit-downs (visitors vs sessions)
VISITOR_COOKIE = "visitor_id"

#--- web analytics ---

# Flask calls before_requests before every route and after_requests after it

@app.before_request
def track_request_start():
    g.start= time.perf_counter() # how long req took
    g.session_id = None
    if request.path.startswith(NOT_TRACKED):
        return

    # visitor id from its cookie or new if it does not exist
    g.visitor_id = request.cookies.get(VISITOR_COOKIE) or uuid.uuid4().hex

    ip = request.headers.get("X-Forwarded-For", request.remote_addr or "").split(",")[0].strip()

    # Physical session id kept in Flask session cookie ("sid"); get_session opens a new one if missing or older than 30 min
    g.session_id = analytics_data.get_session(session.get("sid"), g.visitor_id, ip, request.headers.get("User-Agent", ""))
    session["sid"] = g.session_id

@app.after_request
def track_request_end(response):
    # response exists, we can store status code and time it took
    # dwell beacon not stored as a request: it is background message, not a user action
    if g.get("session_id") and request.path != "/track/dwell":
        analytics_data.save_request(g.session_id, request.method, request.path, request.query_string.decode(errors="ignore"), response.status_code, (time.perf_counter() - g.start) * 1000, request.referrer)
    # first visit: send the visitor cookie to the browser
    if "visitor_id" in g and request.cookies.get(VISITOR_COOKIE) != g.visitor_id:
        response.set_cookie(VISITOR_COOKIE, g.visitor_id, max_age=365 * 24 * 3600, samesite="Lax")
    return response

# Home URL "/"
@app.route('/')
def index():
    print("starting home url /...")

    user_agent = request.headers.get('User-Agent')
    print("Raw user browser:", user_agent)

    user_ip = request.remote_addr
    agent = httpagentparser.detect(user_agent)

    print("Remote IP: {} - JSON user browser {}".format(user_ip, agent))
    return render_template('index.html', page_title="Welcome", methods=METHODS, method=DEFAULT_METHOD)


@app.route('/search', methods=['GET', 'POST'])
def search():
    """
    Search action. The form sends the query with GET (/search?q=...), so the results page has its own URL:
    the browser's back button returns to it without resubmitting a form. POST is kept for old links.
    """
    if request.method == 'POST':
        return redirect(url_for('search', q=request.form.get('search-query', ''),
                                method=request.form.get('method', DEFAULT_METHOD)))

    search_query = request.args.get('q', '').strip()
    if not search_query:
        return redirect(url_for('index'))
    method = request.args.get('method', DEFAULT_METHOD)
    page = max(request.args.get('page', 1, type=int), 1)

    #a new search id only when the query or the method changes, not when the user moves between pages
    same_search = (session.get('last_search_query') == search_query and session.get('last_method') == method
                   and analytics_data.is_session_query(session.get('last_search_id'), g.session_id))
    if not same_search:
        session['last_search_id'] = analytics_data.save_query_terms(search_query, g.session_id, method)
    search_id = session['last_search_id']
    session['last_search_query'] = search_query
    session['last_method'] = method

    #price / rating limits ("under 500", "4+ stars") are not words of the products: we search without them
    #and the RAG checks them on the results. If nothing is left (query "under 500") we search the original text
    constraints = parse_constraints(search_query)
    results = search_engine.search(constraints.search_text or search_query, search_id, corpus, method=method)
    results.query = search_query  #the search box and the page links keep what the user wrote

    found_count = len(results)
    analytics_data.update_query_results(search_id, results.method, results.query_terms, found_count)
    session['last_found_count'] = found_count
    n_pages = max(math.ceil(found_count / RESULTS_PER_PAGE), 1)
    page = min(page, n_pages)
    page_items = results.items[(page - 1) * RESULTS_PER_PAGE: page * RESULTS_PER_PAGE]

    # generate RAG response based on user query and the top retrieved results (only on the first page)
    #all the results are passed (not only the top 20): the improved RAG looks for products that fit the limits
    rag_response = None
    if page == 1 and RAG_MODE == "baseline" and found_count > 0:
        rag_response = rag_generator.generate_response(search_query, results.items, top_N=20)
    elif page == 1 and found_count > 0:
        rag_response = rag_generator.generate_response(search_query, results.items, constraints=constraints)
    if rag_response is not None:
        print("RAG response:", rag_response)

    return render_template('results.html', page_title="Results", results=results, results_list=page_items,
                           found_counter=found_count, rag_response=rag_response, page=page, n_pages=n_pages,
                           methods=METHODS, method=results.method, search_id=search_id)


@app.route('/doc_details', methods=['GET'])
def doc_details():
    """
    Show all the information of one product.
    The link from the results page carries search_id and rank, so we know which search the click came from.
    """
    clicked_doc_id = request.args.get("pid")
    if clicked_doc_id not in corpus:
        abort(404)
    doc: Document = corpus[clicked_doc_id]
    print("click in id={}".format(clicked_doc_id))

    # store data in statistics table 1
    if clicked_doc_id in analytics_data.fact_clicks.keys():
        analytics_data.fact_clicks[clicked_doc_id] += 1
    else:
        analytics_data.fact_clicks[clicked_doc_id] = 1

    rank = request.args.get("rank", type=int)
    click_id = analytics_data.save_click(g.session_id, clicked_doc_id, request.args.get("search_id", type=int), rank)

    #link back to the same results page the user came from
    back_url = None
    if session.get('last_search_query'):
        back_url = url_for('search', q=session['last_search_query'], method=session.get('last_method'))

    return render_template('doc_details.html', page_title=doc.title, doc=doc, back_url=back_url,
                           rank=rank, click_id = click_id)

@app.route('/go', methods=['GET'])
def go_outbound():
    """
    View original webiste link, lets us store the click that leaves our site
    """
    pid = request.args.get("pid")
    if pid not in corpus or not corpus[pid].url:
        abort(404)
    analytics_data.save_click(g.session_id, pid, request.args.get("search_id", type= int), request.args.get("rank", type = int), kind = "outbound")

    return redirect(corpus[pid].url)

@app.route('/track/dwell', methods = ['POST'])
def track_dwell():
    """
    Recieves dwell time from details page
    back button often shows the results page from the browser cache without asking the server, we would not know when the user came back
    """
    data = request.get_json(silent=True) or {}

    try:
        analytics_data.save_dwell(int(data.get("click_id")), float(data.get("seconds")))
    except (TypeError, ValueError):
        pass

    return "", 204


@app.route('/stats', methods=['GET'])
def stats():
    """
    Show simple statistics example. ### Replace with yourdashboard ###
    :return:
    """

    docs = []
    for doc_id in analytics_data.fact_clicks:
        row: Document = corpus[doc_id]
        count = analytics_data.fact_clicks[doc_id]
        doc = StatsDocument(pid=row.pid, title=row.title, description=row.description, url=row.url, count=count)
        docs.append(doc)

    # simulate sort by ranking
    docs.sort(key=lambda doc: doc.count, reverse=True)
    return render_template('stats.html', clicks_data=docs)


@app.route('/dashboard', methods=['GET'])
def dashboard():
    visited_docs = []
    for doc_id in analytics_data.fact_clicks.keys():
        d: Document = corpus[doc_id]
        doc = ClickedDoc(doc_id, d.description, analytics_data.fact_clicks[doc_id])
        visited_docs.append(doc)

    # simulate sort by ranking
    visited_docs.sort(key=lambda doc: doc.counter, reverse=True)

    for doc in visited_docs: print(doc)
    return render_template('dashboard.html', page_title = "Dashboard", visited_docs=visited_docs, data = analytics_data.dashboard_data(corpus, METHODS))


# New route added for generating an examples of basic Altair plot (used for dashboard)
@app.route('/plot_number_of_views', methods=['GET'])
def plot_number_of_views():
    return analytics_data.plot_number_of_views()

@app.route('/analytics/export', methods=['GET'])
def analytics_export():
    """
    All collected tables as JSON
    """
    return jsonify(analytics_data.export())


if __name__ == "__main__":
    app.run(port=8088, host="0.0.0.0", threaded=False, debug=os.getenv("DEBUG"))

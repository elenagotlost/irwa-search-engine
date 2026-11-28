"""
Fills the analytics with simulated visitors and then starts the web app, to test the dashboard.
The analytics are in memory, so the simulation and the server must run in the same process.
Run from the repository root:  python project_progress/part_4/simulate_traffic.py
"""
import os
import random
import sys

# the repository root, so "import web_app" works when running this file from anywhere
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
import web_app  # noqa: E402  (loads corpus, engine and analytics exactly like the real app)

# no LLM calls while simulating: they are slow, cost API quota and are not needed for analytics
web_app.rag_generator.generate_response = lambda *a, **k: None

# different browsers / OS / devices, with public IPs so the country lookup can be tested (GEOIP=1)
USERS = [
    ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36", "8.8.8.8"),
    ("Mozilla/5.0 (X11; Linux x86_64; rv:132.0) Gecko/20100101 Firefox/132.0", "1.1.1.1"),
    ("Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1", "80.58.61.250"),
    ("Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Mobile Safari/537.36", "9.9.9.9"),
    ("Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15", "208.67.222.222"),
]
# each list is a mission: the user refines the same search step by step.
# "silk saree" and "pikachu tshirt" give 0 results (no saree and no pikachu in the corpus)
MISSIONS = [["women kurta", "women cotton kurta", "women cotton kurta blue"],
            ["men jeans", "men slim fit jeans"], ["sweatshirt", "hooded sweatshirt"],
            ["sports shoes"], ["silk saree"], ["pikachu tshirt"], ["men tshirt under 500"]]

random.seed(42)  # same simulation every run
for _ in range(40):
    ua, ip = random.choice(USERS)
    # one Flask test client = one browser with its own cookies, so one visitor / session
    client = web_app.app.test_client()
    client.environ_base.update({"HTTP_USER_AGENT": ua, "REMOTE_ADDR": ip})
    client.get("/")
    for mission in random.sample(MISSIONS, k=random.randint(1, 3)):
        for q in mission[:random.randint(1, len(mission))]:
            method = random.choice(list(web_app.METHODS))
            client.get("/search", query_string={"q": q, "method": method})
            with client.session_transaction() as s:   # search id given by the app to this search
                search_id = s["last_search_id"]
            items = web_app.search_engine.search(q, search_id, web_app.corpus, method=method).items
            for _ in range(random.randint(0, 2)):
                if not items:
                    break
                # real users click the top results much more: exponential distribution of the rank
                rank = min(int(random.expovariate(0.3)) + 1, len(items))
                pid = items[rank - 1].pid
                client.get("/doc_details", query_string={"pid": pid, "search_id": search_id, "rank": rank})
                # what the browser beacon would send when leaving the page (lognormal: a few long visits)
                client.post("/track/dwell", json={"click_id": max(web_app.analytics_data.clicks),
                                                  "seconds": random.lognormvariate(3, 1)})
                if random.random() < 0.2:   # some users go to the original website
                    client.get("/go", query_string={"pid": pid, "search_id": search_id, "rank": rank})

print("Simulated traffic ready: open http://localhost:8088/dashboard")
web_app.app.run(port=8088, host="0.0.0.0", threaded=False)
# Part 4 — RAG, User Interface and Web Analytics

## How to run

1. Install the dependencies (see the main `README.md`) and put `fashion_products_dataset.json` in `data/`.
2. Copy `.env.example` to `.env` and set `GROQ_API_KEY` (free key at https://console.groq.com/keys).
3. From the repository root: `python web_app.py` and open http://localhost:8088.
   The first start builds `data/processed_corpus.pkl` (about a minute); later starts are fast.

## User interface

| File | What it is |
|---|---|
| `../../web_app.py` | Flask app: home, search, results and document details pages |
| `../../myapp/search/search_engine.py` | `SearchEngine.search(query, search_id, corpus, method)`: AND filter of Part 2 + ranking of Part 3, built once at start |
| `../../templates/` | `index.html` (search page), `results.html` (results), `doc_details.html` (whole product) |

### Interface extras (made with AI)

The statement asks for a search page, a results page (title, description, selling price, discount,
average rating, URL) and a details page. To get a better interface, the following extras were added
with the help of an AI assistant:

- Choice of ranking method (our score, BM25, TF-IDF + cosine) under the search box.
- Product image, brand, original price, out-of-stock badge and position on each result.
- Pagination of the results (20 per page), number of results and search time.
- A message explaining why a search has 0 results (which word no product contains).
- Example queries on the home page and a top menu (Search · Dashboard · Stats).
- Styling of the pages (`static/styles/custom.css`).

## RAG

| File | What it is |
|---|---|
| `../../myapp/generation/rag.py` | `BaselineRAGGenerator` (template, unchanged) and `RAGGenerator` (improved) |
| `../../myapp/generation/constraints.py` | Reads price / rating limits and preferences from the query |
| `RAG_NOTES.md` | Weaknesses of the baseline and the three improvements, with pros and cons |
| `rag_comparison.py` | Runs 12 queries through both versions; writes `rag_comparison.md` and `.csv` |

- Model: `openai/gpt-oss-20b` (`GROQ_MODEL` in `.env`); the template's `llama-3.1-8b-instant` was shut down by Groq.
- `RAG_MODE=baseline` in `.env` makes the web app use the template RAG, to compare both.
- Reproduce the comparison: `python project_progress/part_4/rag_comparison.py`
  (LLM answers can change slightly between runs).

## Web analytics

| File | What it is |
|---|---|
| `../../myapp/analytics/analytics_data.py` | `AnalyticsData`: in-memory tables (sessions, requests, queries, clicks) and dashboard data |
| `../../web_app.py` | `before_request` / `after_request` hooks, `/go` (outbound clicks), `/track/dwell`, `/dashboard`, `/analytics/export` |
| `../../templates/dashboard.html` | Dashboard with Chart.js |
| `simulate_traffic.py` | 40 simulated visitors (fixed seed), then starts the app |

- Data is kept in memory and lost when the server stops; `/analytics/export` returns all the tables as JSON.
- Test data for the dashboard: `python project_progress/part_4/simulate_traffic.py`, then open http://localhost:8088/dashboard.
- Country / city lookup is off by default; `GEOIP=1` in `.env` turns it on (sends public IPs to ip-api.com).

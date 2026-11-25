# Part 4 — RAG, User Interface and Web Analytics

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

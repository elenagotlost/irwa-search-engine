# Part 2 — Indexing and Evaluation

## Contents

| File | What it is |
|---|---|
| `part_2.ipynb` | Notebook: builds the inverted index, runs the AND + TF-IDF search, evaluates it on the validation and test queries, and produces every number and figure in the report |
| `../../myapp/search/algorithms.py` | Inverted index, conjunctive (AND) search and TF-IDF ranking (reused by Parts 3–4) |
| `../../myapp/search/evaluation.py` | Evaluation metrics: P@K, R@K, F1@K, AP@K, MAP@K, MRR@K, NDCG@K |
| `test_queries_to_label.csv` | Our five test queries with the top-20 results and our relevance labels |
| `results_validation.csv`, `results_test_queries.csv` | Metric tables written by the notebook |
| `figures/` | Figures produced by the notebook and used in the report |
| `IRWA-2026-u232071-u231981-u232758-part-2.pdf` | Report |

## How to reproduce

1. From the repository root, create and activate the virtual environment and install dependencies
   (see the main `README.md`):
   ```bash
   virtualenv irwa_venv
   source irwa_venv/bin/activate        # Windows: irwa_venv\Scripts\activate.bat
   pip install -r requirements.txt
   ```
2. Put the data files in `data/`:
   - `data/processed_corpus.pkl` — output of Part 1 (if it is missing, the notebook rebuilds it
     from `data/fashion_products_dataset.json` with the Part 1 pipeline)
   - `data/validation_labels.csv`
3. Launch Jupyter and run all cells of `project_progress/part_2/part_2.ipynb`
   (*Kernel → Restart & Run All*). The NLTK resources are downloaded by the first cell.
   Building the index takes about 0.2 s.

Outputs:
- `project_progress/part_2/results_validation.csv`, `project_progress/part_2/results_test_queries.csv`
- `project_progress/part_2/figures/*.png`

## Using the search engine from code

```python
import pandas as pd
from myapp.search.algorithms import create_index, search_in_corpus

corpus = pd.read_pickle("data/processed_corpus.pkl")
index, tf, idf = create_index(corpus)
search_in_corpus("women full sleeve sweatshirt cotton", index, tf, idf, k=10)
# [(pid, score), ...] sorted by decreasing score, ties broken by pid
```

- `create_index(corpus)` indexes the `all_tokens` column and returns `index` (term → list of pids),
  `tf` (term → {pid: count / ‖d‖}) and `idf` (term → log(N / df)).
- `conjunctive_search(query_terms, index)` returns the set of pids that contain **all** the query terms.
- `rank_documents(query_terms, docs, tf, idf)` scores the candidates with the TF-IDF dot product.
- `search_in_corpus(query, index, tf, idf, k=20)` chains the three steps; the query goes through
  the same `preprocess_text` as the documents. `k=None` returns all matches.

## Evaluating

```python
from myapp.search.evaluation import get_labels_and_scores, precision_at_k, map_at_k

labels = pd.read_csv("data/validation_labels.csv")
y_true, y_score = get_labels_and_scores("men slim jeans blue",
                                        labels[labels.query_id == 2], index, tf, idf)
precision_at_k(y_true, y_score, k=10)
```

- Every metric takes `y_true` (label of each judged product) and `y_score` (our score for it), as in
  the labs. Judged products that the AND search does not return get score 0 and never count as retrieved.
- `map_at_k` and `mrr_at_k` take a list of `(y_true, y_score)` pairs, one per query.
- `AP@K` is divided by the number of relevant products found in the top K (lab version), not by R.
- For our test queries the notebook uses `y_score = 1 / rank`, so the metrics follow the order in
  which the products were returned; R counts only the relevant products within the judged top 20.

## Test queries

| # | Query | AND matches | Relevant / judged |
|---|---|---|---|
| 1 | men cotton polo tshirt | 1,213 | 19 / 20 |
| 2 | women cotton kurta | 358 | 20 / 20 |
| 3 | men hooded sweatshirt | 323 | 20 / 20 |
| 4 | men running shoes | 37 | 11 / 20 |
| 5 | women blue denim jacket | 27 | 13 / 20 |

`test_queries_to_label.csv` columns: `query_id`, `query`, `rank`, `pid`, `title`, `fabric`, `color`, `label`
(1 = relevant, 0 = not relevant). The labelling criteria are described in Section 2.3 of the report.
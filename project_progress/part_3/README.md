# Part 3 — Ranking and Filtering

## Contents

| File | What it is |
|---|---|
| `part_3.ipynb` | Notebook: ranks the AND matches of our five test queries with TF-IDF + cosine, BM25, our score and word2vec + cosine, and produces every number in the report |
| `../../myapp/search/ranking.py` | TF-IDF + cosine and BM25 (`search_ranked`) |
| `../../myapp/search/custom_score.py` | Our score: BM25 × title, rating, stock and discount factors (`search_custom`) |
| `../../myapp/search/word2vec_score.py` | word2vec (skip-gram with negative sampling, numpy) + cosine ranking (`search_word2vec`) |
| `IRWA-2026-u232071-u231981-u232758-part-3.pdf` | Report |

All methods use the same AND filter from Part 2 (`conjunctive_search`): only the order of the results changes.

## How to reproduce

1. From the repository root, create and activate the virtual environment and install dependencies
   (see the main `README.md`):
   ```bash
   virtualenv irwa_venv
   source irwa_venv/bin/activate        # Windows: irwa_venv\Scripts\activate.bat
   pip install -r requirements.txt
   ```
2. Put the data files in `data/`:
   - `data/processed_corpus.pkl` — output of Part 1
   - `project_progress/part_2/test_queries_to_label.csv` (already in the repo) is used for the Part 2 labels
3. Launch Jupyter and run all cells of `project_progress/part_3/part_3.ipynb`
   (*Kernel → Restart & Run All*).
   The first run trains word2vec (a few minutes) and saves the vectors to `data/word2vec_vectors.npz`;
   later runs load them. The seed is fixed (42), so the vectors and the rankings are always the same.

## Choosing a ranking method from code

```python
import pandas as pd
from myapp.search.algorithms import create_index
from myapp.search.ranking import create_ranking_data, search_ranked
from myapp.search.custom_score import create_custom_data, search_custom
from myapp.search.word2vec_score import train_word2vec, create_word2vec_data, search_word2vec

corpus = pd.read_pickle("data/processed_corpus.pkl")
index, tf, idf = create_index(corpus)
data = create_ranking_data(corpus, idf)

search_ranked("men running shoes", index, idf, data, method="tfidf", k=20)   # TF-IDF + cosine
search_ranked("men running shoes", index, idf, data, method="bm25", k=20)    # BM25 (k1 = 1.2, b = 0.75)

custom_data = create_custom_data(corpus)
search_custom("men running shoes", index, idf, data, custom_data, k=20)      # our score

w2v_data = create_word2vec_data(corpus, train_word2vec(corpus))
search_word2vec("men running shoes", index, w2v_data, k=20)                  # word2vec + cosine
# each returns [(pid, score), ...] sorted by decreasing score, ties broken by pid; k=None returns all matches
```

- BM25 parameters: `rank_bm25(query_terms, docs, idf, data, k1=1.2, b=0.75)`.
- Our score's weights are constants at the top of `custom_score.py`
  (`TITLE_WEIGHT`, `RATING_WEIGHT`, `OUT_OF_STOCK_FACTOR`, `DISCOUNT_WEIGHT`).
- word2vec parameters are constants at the top of `word2vec_score.py`
  (`VECTOR_SIZE`, `WINDOW`, `MIN_COUNT`, `NEGATIVE`, `EPOCHS`, `SEED`).
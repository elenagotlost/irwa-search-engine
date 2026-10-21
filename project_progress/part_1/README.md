# Part 1 — Text Processing and Exploratory Data Analysis

## Contents

| File | What it is |
|---|---|
| `part_1.ipynb` | Notebook: runs the pre-processing, justifies the field decisions with data, and performs the EDA |
| `../../myapp/core/preprocessing.py` | The pre-processing pipeline (reused by Parts 2–4 for documents and queries) |
| `figures/` | Figures produced by the notebook and used in the report |
| `IRWA-2026-uXXXXXX-uXXXXXX-uXXXXXX-part-1.pdf` | Report |

## How to reproduce

1. From the repository root, create and activate the virtual environment and install dependencies
   (see the main `README.md`):
   ```bash
   virtualenv irwa_venv
   source irwa_venv/bin/activate        # Windows: irwa_venv\Scripts\activate.bat
   pip install -r requirements.txt
   python -m spacy download en_core_web_sm   # only needed for the NER cell
   ```
2. Put the two data files in `data/`:
   - `data/fashion_products_dataset.json`
   - `data/validation_labels.csv`
3. Launch Jupyter and run all cells of `project_progress/part_1/part_1.ipynb`
   (*Kernel → Restart & Run All*). The NLTK resources (`stopwords`, `punkt`, `punkt_tab`)
   are downloaded by the first cell. A full run takes about one minute.

Outputs:
- `data/processed_corpus.pkl` — the processed corpus (one row per product), input for Part 2
- `project_progress/part_1/figures/*.png`

## Using the pipeline from code

```python
from myapp.core.preprocessing import load_raw_corpus, preprocess_corpus, preprocess_text

corpus = preprocess_corpus(load_raw_corpus("data/fashion_products_dataset.json"))
preprocess_text("women full sleeve sweatshirt cotton")
# ['women', 'full', 'sleev', 'sweatshirt', 'cotton']
```

Options:
- `preprocess_text(text, use_stemming=False)` / `preprocess_corpus(df, use_stemming=False)`
  return un-stemmed tokens (used for the word clouds).
- The stop-word list, domain normalisations (`PHRASE_NORMALISATION`, `COMPOUND_SPLITS`) and the
  `product_details` keys excluded from the text (`DETAIL_KEYS_TO_DROP`) are constants at the top
  of `preprocessing.py`.

## Processed corpus columns

| Column(s) | Content |
|---|---|
| `pid`, `title`, `description`, `brand`, `category`, `sub_category`, `product_details`, `seller`, `out_of_stock`, `selling_price`, `discount`, `actual_price`, `average_rating`, `url` | Original values, returned to the user (`product_details` flattened to a dict) |
| `title_tokens`, `description_tokens`, `details_tokens`, `brand_tokens` | Processed terms per field (for a fielded index / field weighting) |
| `all_tokens` | Concatenation of the four lists above (for a single combined index) |
| `brand_kw`, `seller_kw`, `category_kw`, `sub_category_kw` | Normalised keywords for filtering |
| `selling_price_num`, `actual_price_num`, `discount_num`, `average_rating_num` | Parsed numbers (not indexed as text) |
| `has_rating`, `price_imputed` | Flags for products without rating / without list price |

# Part 4 — RAG: baseline vs improved

Code: `myapp/generation/rag.py` (both generators), `myapp/generation/constraints.py` (query limits).
The web app uses the improved one; set `RAG_MODE=baseline` in `.env` to see the template one.

## Weaknesses of the baseline

1. **The LLM only sees `PID + title`.** The prompt asks it to justify the choice "referring to price,
   features, quality", but price, rating, discount, stock, brand and product details are never sent.
   Any price or quality it mentions is made up.
2. **Limits in the query are lost.** Our preprocessing removes "under", "above" and numbers, so
   "kurta under 500" searches "kurta" and the top 20 can all cost more than 500. Words like "rs",
   "rating", "stars" or "cheap" are worse: they become AND terms almost no product has → 0 results.
3. **Only the top 20 by text score are considered**, even when a product that fits the limit is at rank 150.
4. **Out-of-stock products can be recommended.**
5. **Free-text answer, nothing checked.** The model can write a PID that was never retrieved (or
   change one character), and the page can't link to the product. Default temperature → different
   answer each time for the same query.
6. **"No good products" is left to an 8B model**, which tends to always pick something.

## Improvements

### 1. Rich product context
Each product is sent as a numbered block: title, brand, category > sub-category, price (list price and
% off), rating (or "not rated yet"), up to 8 product details (Fabric, Color, Fit, Pattern... first;
codes, care text and long values dropped) and the first 250 characters of the description.
We send 10 products instead of 20, so the prompt stays a similar size.

* Pros: the model can actually compare on price / rating / material; explanations cite real facts.
* Cons: more tokens per product, so fewer products fit; detail keys vary by category, so the
  priority list doesn't fit everything (e.g. shoes).

### 2. Query constraints and "no good products" handled in code
`parse_constraints()` reads max/min price ("under 500", "rs 300-600", "between 1000 and 2000"), a
minimum rating ("4+ stars", "rating above 4", "rated 4 or more") and preferences ("cheap",
"top rated"). The web app searches without those words. The RAG then walks **all** the matches in
ranking order, keeps the ones in stock that meet the limits, and sends the top 10 (with a preference,
the first 30 that fit are re-sorted by price / rating).
If none fit, **the LLM is not called**: the answer says which limit failed and gives the closest
product (e.g. cheapest one), computed in Python. The one-line overview of the results (how many fit,
price range, how many rated 4+) is also computed in Python.

* Pros: limits are always respected (checked in code, not by the model); finds fitting products
  past rank 20; fixes searches that returned 0 results; no LLM cost when nothing fits; honest answer.
* Cons: regex rules only cover common phrasings ("under 4 stars" is read as ≥ 4); products with no
  rating are excluded when a rating limit is given; strict limits (Rs. 501 is out for "under 500").

### 3. Structured, grounded answer
A system prompt with explicit rules (only use the listed products and facts; prefer the right product
type/gender; say null instead of forcing a pick), temperature 0.2, and JSON mode:
`{"best": {"ref", "why"}, "alternative": {"ref", "why"}, "no_match_reason"}`.
Each `ref` is checked against the list we sent; an invalid one is dropped, so the page can only show
products that were really retrieved, with a link to our details page, and price / rating shown from
the corpus, not from the model. Answers are cached per query + product list.

* Pros: no invented PIDs; the results page shows a clean card with links; same query → same answer;
  the model can refuse when the products are the wrong type (e.g. "women" products for a "men" query).
* Cons: JSON mode can fail on some models (we retry without it, and show the raw text if it is not
  JSON); a stricter format leaves less room for a longer, nuanced explanation.

## Examples for the report

With `GROQ_API_KEY` in `.env` and the data in `data/`, from the repo root:

```bash
python project_progress/part_4/rag_comparison.py
```

It runs 12 queries (the five test queries + queries with limits, preferences and impossible limits)
through both systems and writes `rag_comparison.md` (answers side by side) and `rag_comparison.csv`.
For each answer it checks automatically: recommended PID is among the retrieved products, product
fits the query limits and is in stock, system said "no match", time and prompt tokens.

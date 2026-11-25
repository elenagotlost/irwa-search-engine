"""
Baseline RAG vs improved RAG on the same queries (Part 4 report).

Run from the repository root, with GROQ_API_KEY in .env and the data in data/:
    python project_progress/part_4/rag_comparison.py
    python project_progress/part_4/rag_comparison.py "men running shoes under 1000" "red saree"

Each system runs end to end as in the web app:
* baseline: search with the query as written -> top 20 titles -> template prompt
* improved: search without the price / rating words -> limits checked on all matches -> top 10 with full data

For each answer we check automatically:
* valid_pid:  the recommended product is one of the products the search returned
* fits:       the recommended product is in stock and meets the price / rating limits of the query
* no_match:   the system said that no product fits
Outputs: rag_comparison.md (to read / copy examples into the report) and rag_comparison.csv
"""
import os
import re
import sys
import time

import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)
os.chdir(ROOT)

from dotenv import load_dotenv  # noqa: E402

from myapp.generation.constraints import parse_constraints  # noqa: E402
from myapp.generation.rag import BaselineRAGGenerator, RAGGenerator  # noqa: E402
from myapp.search.load_corpus import load_corpus  # noqa: E402
from myapp.search.search_engine import SearchEngine  # noqa: E402

load_dotenv()

#the five test queries of Parts 2-3, plus queries with limits, preferences and impossible requests
QUERIES = [
    "men cotton polo tshirt",
    "women cotton kurta",
    "men hooded sweatshirt",
    "men running shoes",
    "women blue denim jacket",
    "women cotton kurta under 500",
    "men running shoes rating above 4",
    "cheap black jeans for women",
    "top rated men hooded sweatshirt",
    "men polo tshirt between 300 and 600 rs",
    "men hooded sweatshirt under 100",
    "women denim jacket 5 stars under 300",
]
PID = re.compile(r"\b[A-Z0-9]{16}\b")
OUT_DIR = os.path.dirname(os.path.abspath(__file__))


def check(pid, results, corpus, constraints):
    """valid_pid and fits for one recommended product (None when nothing was recommended)."""
    if pid is None:
        return None, None
    valid = pid in {r.pid for r in results}
    doc = corpus.get(pid)
    if doc is None:
        return valid, False
    fits = not constraints.check(doc.selling_price, doc.average_rating) and not doc.out_of_stock
    return valid, fits


def main(queries):
    corpus = load_corpus(os.path.join(ROOT, os.getenv("DATA_FILE_PATH", "data/fashion_products_dataset.json")))
    engine = SearchEngine(os.path.join(ROOT, os.getenv("PROCESSED_CORPUS_PATH", "data/processed_corpus.pkl")),
                          os.path.join(ROOT, os.getenv("DATA_FILE_PATH", "data/fashion_products_dataset.json")))
    baseline, improved = BaselineRAGGenerator(), RAGGenerator(corpus)

    rows, md = [], ["# Baseline vs improved RAG\n",
                    f"Model: `{improved.model}`. Generated {time.strftime('%Y-%m-%d %H:%M')}.\n"]
    for q in queries:
        constraints = parse_constraints(q)

        base_results = engine.search(q, 0, corpus).items
        t = time.perf_counter()
        base_text = baseline.generate_response(q, base_results, top_N=20) if base_results else "(no results, RAG not called)"
        base_time = time.perf_counter() - t
        base_pids = PID.findall(base_text)
        base_pid = base_pids[0] if base_pids else None
        base_valid, base_fits = check(base_pid, base_results, corpus, constraints)

        imp_results = engine.search(constraints.search_text or q, 0, corpus).items
        imp = improved.generate_response(q, imp_results, constraints=constraints)
        imp_pid = imp.best.pid if imp.best else None
        imp_valid, imp_fits = check(imp_pid, imp_results, corpus, constraints)

        for system, n, pid, valid, fits, no_match, secs, tokens in [
            ("baseline", len(base_results), base_pid, base_valid, base_fits,
             "no good products" in base_text.lower(), base_time, getattr(baseline.last_usage, "prompt_tokens", None)),
            ("improved", len(imp_results), imp_pid, imp_valid, imp_fits,
             imp.status in ("no_match", "no_results"), imp.latency, imp.prompt_tokens),
        ]:
            rows.append(dict(query=q, system=system, n_results=n, recommended_pid=pid, valid_pid=valid, fits=fits,
                             no_match=no_match, seconds=round(secs, 2), prompt_tokens=tokens))

        md.append(f"## `{q}`\n")
        md.append(f"Limits understood: {constraints.describe() or 'none'} · search text for improved: "
                  f"`{constraints.search_text or q}`\n")
        md.append(f"**Baseline** ({len(base_results):,} results, valid PID: {base_valid}, fits limits: {base_fits})\n")
        md.append("```\n" + base_text.strip() + "\n```\n")
        md.append(f"**Improved** ({len(imp_results):,} results, status `{imp.status}`, valid PID: {imp_valid}, "
                  f"fits limits: {imp_fits})\n")
        md.append("```\n" + imp.text.strip() + "\n```\n")
        print(f"done: {q}")
        time.sleep(1)  #stay under the free-tier rate limit

    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(OUT_DIR, "rag_comparison.csv"), index=False)
    summary = df.groupby("system").agg(
        queries=("query", "count"),
        recommended=("recommended_pid", lambda s: s.notna().sum()),
        valid_pid=("valid_pid", lambda s: (s == True).sum()),  # noqa: E712
        fits_limits=("fits", lambda s: (s == True).sum()),  # noqa: E712
        said_no_match=("no_match", "sum"),
        mean_seconds=("seconds", "mean"),
        mean_prompt_tokens=("prompt_tokens", "mean"),
    ).round(2)
    md.insert(2, "## Summary\n\n```\n" + summary.to_string() + "\n```\n")
    with open(os.path.join(OUT_DIR, "rag_comparison.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(md))
    print(summary)
    print(f"\nSaved rag_comparison.md and rag_comparison.csv in {OUT_DIR}")


if __name__ == "__main__":
    main(sys.argv[1:] or QUERIES)

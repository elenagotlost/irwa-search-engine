import os
import time

import pandas as pd

from myapp.core.preprocessing import load_raw_corpus, preprocess_corpus, preprocess_text
from myapp.search.algorithms import conjunctive_search, create_index
from myapp.search.custom_score import create_custom_data, rank_custom
from myapp.search.objects import ResultItem
from myapp.search.ranking import create_ranking_data, rank_bm25, rank_tfidf_cosine

#ranking methods the web app can use (Part 3). Our score is the default because it gave the best top 20
METHODS = {
    "custom": "Our score",
    "bm25": "BM25",
    "tfidf": "TF-IDF + cosine",
}
DEFAULT_METHOD = "custom"


def load_processed_corpus(processed_path, raw_path):
    """
    Load the processed corpus of Part 1. If the pickle is missing, build it from the raw JSON
    with the Part 1 pipeline and save it, so the next start is fast.
    """
    if os.path.exists(processed_path):
        return pd.read_pickle(processed_path)
    print("Processed corpus not found, building it from the raw JSON (this takes about a minute)...")
    corpus = preprocess_corpus(load_raw_corpus(raw_path))
    corpus.to_pickle(processed_path)
    return corpus


class SearchResults:
    """
    The answer of one search: the ranked list of products plus what the results page needs to explain it.
    """

    def __init__(self, query, method, items, query_terms, missing_terms, elapsed):
        self.query = query
        self.method = method
        self.items = items                  #list of ResultItem, best first
        self.query_terms = query_terms      #processed terms used for the AND
        self.missing_terms = missing_terms  #terms that no product contains (they make the AND empty)
        self.elapsed = elapsed              #search time in seconds

    def __len__(self):
        return len(self.items)


class SearchEngine:
    """
    Search engine of Parts 2 and 3, prepared for the web app.
    Everything that does not depend on the query (index, idf, document lengths, factors of our score)
    is computed once when the app starts, so a search only touches the products returned by the AND.
    """

    def __init__(self, processed_path, raw_path):
        start = time.perf_counter()
        corpus = load_processed_corpus(processed_path, raw_path)
        self.index, _, self.idf = create_index(corpus)
        self.ranking_data = create_ranking_data(corpus, self.idf)
        self.custom_data = create_custom_data(corpus)
        print(f"Search engine ready: {len(corpus):,} products, {len(self.idf):,} terms "
              f"({time.perf_counter() - start:.1f} s)")

    def rank(self, query_terms, docs, method):
        if method == "bm25":
            return rank_bm25(query_terms, docs, self.idf, self.ranking_data)
        if method == "tfidf":
            return rank_tfidf_cosine(query_terms, docs, self.idf, self.ranking_data)
        return rank_custom(query_terms, docs, self.idf, self.ranking_data, self.custom_data)

    def search(self, search_query, search_id, corpus, method=DEFAULT_METHOD):
        """
        General search function: preprocess the query, keep the products with ALL its terms (AND)
        and rank them.
        :param search_query: query text as written by the user
        :param search_id: id of the search (analytics), added to the result links
        :param corpus: pid -> Document, used to fill in the fields shown on the results page
        :param method: "custom" (our score), "bm25" or "tfidf"
        :return: SearchResults with all the matching products, best first
        """
        start = time.perf_counter()
        if method not in METHODS:
            method = DEFAULT_METHOD

        query_terms = preprocess_text(search_query)
        #a term that no product contains makes the AND empty: we tell the user which one it is
        missing_terms = [t for t in query_terms if t not in self.index]

        ranked = []
        if query_terms and not missing_terms:
            docs = conjunctive_search(query_terms, self.index)
            ranked = self.rank(query_terms, docs, method)

        items = []
        for position, (pid, score) in enumerate(ranked, start=1):
            doc = corpus[pid]
            items.append(ResultItem(
                pid=pid,
                title=doc.title,
                description=doc.description,
                #link to our details page; search_id and rank let the analytics know where the click came from
                url=f"doc_details?pid={pid}&search_id={search_id}&rank={position}",
                original_url=doc.url,
                ranking=score,
                rank=position,
                brand=doc.brand,
                selling_price=doc.selling_price,
                actual_price=doc.actual_price,
                discount=doc.discount,
                average_rating=doc.average_rating,
                out_of_stock=doc.out_of_stock,
                image=doc.images[0] if doc.images else None,
            ))

        return SearchResults(search_query, method, items, query_terms, missing_terms,
                             time.perf_counter() - start)

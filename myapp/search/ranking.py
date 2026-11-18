import math
from collections import Counter

from myapp.core.preprocessing import preprocess_text
from myapp.search.algorithms import conjunctive_search


def tfidf_weight(count, idf):
    """
    Weight of a term in a text, as in the lectures: (1 + log2(f)) * idf.
    :param count: times the term appears in the text
    :param idf: idf of the term
    """
    if count == 0:
        return 0
    return (1 + math.log2(count)) * idf


def create_ranking_data(corpus, idf):
    """
    Precompute what TF-IDF + cosine and BM25 need for every document.
    :param corpus: dataframe with the columns 'pid' and 'all_tokens'
    :param idf: term -> idf, from create_index (Part 2)
    :return: dict with the term counts, the length of the tf-idf vector and the number of tokens of
             every document, and the average number of tokens
    """
    counts = {}
    doc_norms = {}
    doc_lengths = {}
    for pid, tokens in zip(corpus["pid"], corpus["all_tokens"]):
        term_counts = Counter(tokens)
        counts[pid] = term_counts
        #length of the full tf-idf vector of the document (all its terms, not only the query ones)
        doc_norms[pid] = math.sqrt(sum(tfidf_weight(c, idf[t]) ** 2 for t, c in term_counts.items()))
        doc_lengths[pid] = len(tokens)

    return {
        "counts": counts,
        "doc_norms": doc_norms,
        "doc_lengths": doc_lengths,
        "avg_length": sum(doc_lengths.values()) / len(doc_lengths),
    }


def sort_scores(scores):
    #highest score first, and by pid when two scores are equal (same rule as Part 2)
    scores.sort(key=lambda x: (-x[1], x[0]))
    return scores


def rank_tfidf_cosine(query_terms, docs, idf, data):
    """
    Rank documents with TF-IDF + cosine similarity.
    score = (query vector . document vector) / (||query|| * ||document||)
    :param query_terms: list of processed query terms
    :param docs: pids to rank (output of conjunctive_search)
    :param data: output of create_ranking_data
    :return: list of (pid, score) sorted from best to worst
    """
    query_weights = {t: tfidf_weight(c, idf[t]) for t, c in Counter(query_terms).items()}
    query_norm = math.sqrt(sum(w ** 2 for w in query_weights.values()))

    scores = []
    for pid in docs:
        dot = 0
        for term, query_weight in query_weights.items():
            dot += query_weight * tfidf_weight(data["counts"][pid][term], idf[term])
        norms = query_norm * data["doc_norms"][pid]
        scores.append((pid, dot / norms if norms > 0 else 0))
    return sort_scores(scores)


def rank_bm25(query_terms, docs, idf, data, k1=1.2, b=0.75):
    """
    Rank documents with BM25 (the RSV formula of the lectures).
    score = sum over the query terms of idf * (k1 + 1) * tf / (k1 * ((1 - b) + b * L_d / L_ave) + tf)
    :param query_terms: list of processed query terms
    :param docs: pids to rank (output of conjunctive_search)
    :param data: output of create_ranking_data
    :param k1: how fast the gain of repeating a term saturates
    :param b: how much the length of the document is penalised (0 = not at all, 1 = fully)
    :return: list of (pid, score) sorted from best to worst
    """
    scores = []
    for pid in docs:
        length_part = k1 * ((1 - b) + b * data["doc_lengths"][pid] / data["avg_length"])
        score = 0
        for term in set(query_terms):
            tf = data["counts"][pid][term]
            score += idf[term] * (k1 + 1) * tf / (length_part + tf)
        scores.append((pid, score))
    return sort_scores(scores)


def search_ranked(query, index, idf, data, method="bm25", k=20):
    """
    Full search: preprocess the query, keep the documents with ALL the terms and rank them.
    :param query: query text as written by the user
    :param method: "tfidf" (TF-IDF + cosine) or "bm25"
    :param k: number of results to return (None = all)
    :return: list of (pid, score) with the top k results
    """
    query_terms = preprocess_text(query)
    if not query_terms:
        return []

    docs = conjunctive_search(query_terms, index)
    if method == "tfidf":
        ranked = rank_tfidf_cosine(query_terms, docs, idf, data)
    elif method == "bm25":
        ranked = rank_bm25(query_terms, docs, idf, data)
    else:
        raise ValueError(f"unknown ranking method: {method}")

    if k is None:
        return ranked
    return ranked[:k]

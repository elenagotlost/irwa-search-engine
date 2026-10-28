import math
from collections import Counter, defaultdict

from myapp.core.preprocessing import preprocess_text


def create_index(corpus):
    """
    Build the inverted index and the tf / idf values from the processed corpus (Part 1).
    :param corpus: dataframe with the columns 'pid' and 'all_tokens'
    :return: index (term -> list of pids), tf (term -> {pid: normalised tf}), idf (term -> idf)
    """
    index = defaultdict(list)
    tf = defaultdict(dict)
    df = defaultdict(int)

    for pid, tokens in zip(corpus["pid"], corpus["all_tokens"]):
        counts = Counter(tokens)
        #we normalise tf by the length of the document vector, so long descriptions don't win just for being long
        norm = math.sqrt(sum(c * c for c in counts.values()))
        for term, count in counts.items():
            index[term].append(pid)
            tf[term][pid] = count / norm
            df[term] += 1

    n_docs = len(corpus)
    idf = {term: math.log(n_docs / df[term]) for term in df}
    return index, tf, idf


def conjunctive_search(query_terms, index):
    """
    Return the pids of the documents that contain ALL the query terms (AND query).
    :param query_terms: list of processed query terms
    :param index: inverted index from create_index
    :return: set of pids
    """
    docs = None
    for term in query_terms:
        #if one term is not in the vocabulary no document can contain all of them
        if term not in index:
            return set()
        if docs is None:
            docs = set(index[term])
        else:
            docs = docs & set(index[term])
    return docs if docs else set()


def rank_documents(query_terms, docs, tf, idf):
    """
    Rank the documents with tf-idf: score = dot product between the query vector and the document vector.
    :param query_terms: list of processed query terms
    :param docs: pids to rank (output of conjunctive_search)
    :return: list of (pid, score) sorted from best to worst
    """
    query_counts = Counter(query_terms)
    query_norm = math.sqrt(sum(c * c for c in query_counts.values()))

    scores = []
    for pid in docs:
        score = 0
        for term, count in query_counts.items():
            query_weight = count / query_norm * idf[term]
            doc_weight = tf[term][pid] * idf[term]
            score += query_weight * doc_weight
        scores.append((pid, score))

    #sort by score, and by pid when two scores are equal so the order is always the same
    scores.sort(key=lambda x: (-x[1], x[0]))
    return scores


def search_in_corpus(query, index, tf, idf, k=20):
    """
    Full search: preprocess the query, find the documents with all the terms and rank them.
    :param query: query text as written by the user
    :param k: number of results to return (None = all)
    :return: list of (pid, score) with the top k results
    """
    #the query goes through the same preprocessing as the documents, or the terms won't match
    query_terms = preprocess_text(query)
    if not query_terms:
        return []

    docs = conjunctive_search(query_terms, index)
    ranked = rank_documents(query_terms, docs, tf, idf)
    if k is None:
        return ranked
    return ranked[:k]

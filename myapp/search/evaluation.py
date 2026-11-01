import numpy as np

from myapp.search.algorithms import search_in_corpus


def get_labels_and_scores(query, labels, index, tf, idf):
    """
    Get the relevance labels and our tf-idf scores for the labelled documents of one query.
    Documents that our AND search doesn't return get score 0.
    :param query: query text
    :param labels: dataframe with the columns 'pid' and 'labels' for this query
    :return: y_true, y_score (numpy arrays in the same order)
    """
    scores = dict(search_in_corpus(query, index, tf, idf, k=None))
    y_true = labels["labels"].to_numpy()
    y_score = np.array([scores.get(pid, 0) for pid in labels["pid"]])
    return y_true, y_score


def top_k_labels(y_true, y_score, k):
    #stable sort: documents with the same score keep their original order
    order = np.argsort(-y_score, kind="stable")
    #score 0 means our AND search didn't return the document, so it can't count as retrieved
    order = order[y_score[order] > 0]
    return y_true[order][:k]


def precision_at_k(y_true, y_score, k=10):
    top = top_k_labels(y_true, y_score, k)
    return np.sum(top) / k


def recall_at_k(y_true, y_score, k=10):
    total_relevant = np.sum(y_true)
    if total_relevant == 0:
        return 0
    return np.sum(top_k_labels(y_true, y_score, k)) / total_relevant


def f1_at_k(y_true, y_score, k=10):
    p = precision_at_k(y_true, y_score, k)
    r = recall_at_k(y_true, y_score, k)
    if p + r == 0:
        return 0
    return 2 * p * r / (p + r)


def avg_precision_at_k(y_true, y_score, k=10):
    top = top_k_labels(y_true, y_score, k)
    precisions = []
    relevant_so_far = 0
    for i, label in enumerate(top):
        if label == 1:
            relevant_so_far += 1
            precisions.append(relevant_so_far / (i + 1))
    if relevant_so_far == 0:
        return 0
    return sum(precisions) / relevant_so_far


def rr_at_k(y_true, y_score, k=10):
    top = top_k_labels(y_true, y_score, k)
    if np.sum(top) == 0:
        return 0
    return 1 / (np.argmax(top) + 1)


def dcg_at_k(y_true, y_score, k=10):
    top = top_k_labels(y_true, y_score, k)
    discounts = np.log2(np.arange(len(top)) + 2)
    return np.sum(top / discounts)


def ndcg_at_k(y_true, y_score, k=10):
    #the ideal ranking is the labels sorted from most to least relevant
    ideal = dcg_at_k(y_true, y_true, k)
    if ideal == 0:
        return 0
    return dcg_at_k(y_true, y_score, k) / ideal


def map_at_k(queries, k=10):
    """
    :param queries: list of (y_true, y_score), one for each query
    """
    return np.mean([avg_precision_at_k(y_true, y_score, k) for y_true, y_score in queries])


def mrr_at_k(queries, k=10):
    """
    :param queries: list of (y_true, y_score), one for each query
    """
    return np.mean([rr_at_k(y_true, y_score, k) for y_true, y_score in queries])

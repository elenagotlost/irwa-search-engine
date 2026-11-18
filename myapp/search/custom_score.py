import math

from myapp.core.preprocessing import preprocess_text
from myapp.search.algorithms import conjunctive_search
from myapp.search.ranking import rank_bm25

#how much a product that has all the query terms in its title is boosted (x2 at most)
TITLE_WEIGHT = 1.0
#how much the rating moves the score: a 5.0 gets about +9%, a 1.0 about -18%
RATING_WEIGHT = 0.25
#out of stock products are pushed down, not removed (Part 1 decision)
OUT_OF_STOCK_FACTOR = 0.5
#small bonus for discounts: list prices of cheap products are often inflated (Part 1 EDA)
DISCOUNT_WEIGHT = 0.2


def create_custom_data(corpus):
    """
    Precompute the fields our score needs for every product.
    :param corpus: processed corpus from Part 1
    :return: dict with pid -> {title terms, rating, out_of_stock, discount} and the mean rating
    """
    products = {}
    for row in corpus[["pid", "title_tokens", "average_rating_num", "out_of_stock", "discount_num"]].itertuples(index=False):
        rating = row.average_rating_num
        discount = row.discount_num
        products[row.pid] = {
            "title": set(row.title_tokens),
            #NaN means the product has no rating
            "rating": None if math.isnan(rating) else rating,
            "out_of_stock": bool(row.out_of_stock),
            "discount": 0 if math.isnan(discount) else discount,
        }
    return {"products": products, "mean_rating": corpus["average_rating_num"].mean()}


def custom_factors(pid, query_terms, custom_data):
    """
    The four factors that multiply the BM25 score of one product.
    :return: dict with the value of each factor
    """
    product = custom_data["products"][pid]
    mean_rating = custom_data["mean_rating"]
    terms = set(query_terms)

    #share of the query terms that appear in the title (the most discriminative field in Part 1)
    title = 1 + TITLE_WEIGHT * len(terms & product["title"]) / len(terms)

    #relative distance to the mean rating, with a small weight: there is no number of reviews,
    #so a 5.0 may come from one review. Products without rating are neutral (factor 1)
    if product["rating"] is None:
        rating = 1
    else:
        rating = 1 + RATING_WEIGHT * (product["rating"] - mean_rating) / mean_rating

    stock = OUT_OF_STOCK_FACTOR if product["out_of_stock"] else 1
    discount = 1 + DISCOUNT_WEIGHT * product["discount"] / 100

    return {"title": title, "rating": rating, "stock": stock, "discount": discount}


def rank_custom(query_terms, docs, idf, data, custom_data):
    """
    Our score: BM25 multiplied by the title, rating, stock and discount factors.
    score = bm25 * title * rating * stock * discount
    :param query_terms: list of processed query terms
    :param docs: pids to rank (output of conjunctive_search)
    :param data: output of create_ranking_data (ranking.py)
    :param custom_data: output of create_custom_data
    :return: list of (pid, score) sorted from best to worst
    """
    scores = []
    for pid, bm25 in rank_bm25(query_terms, docs, idf, data):
        factors = custom_factors(pid, query_terms, custom_data)
        score = bm25
        for value in factors.values():
            score *= value
        scores.append((pid, score))

    #highest score first, and by pid when two scores are equal
    scores.sort(key=lambda x: (-x[1], x[0]))
    return scores


def search_custom(query, index, idf, data, custom_data, k=20):
    """
    Full search with our score: preprocess the query, AND filter and rank.
    :param k: number of results to return (None = all)
    :return: list of (pid, score) with the top k results
    """
    query_terms = preprocess_text(query)
    if not query_terms:
        return []

    docs = conjunctive_search(query_terms, index)
    ranked = rank_custom(query_terms, docs, idf, data, custom_data)
    if k is None:
        return ranked
    return ranked[:k]

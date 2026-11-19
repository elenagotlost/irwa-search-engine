import numpy as np
from collections import Counter

from myapp.core.preprocessing import preprocess_text
from myapp.search.algorithms import conjunctive_search
from myapp.search.ranking import sort_scores

#size of the word vectors
VECTOR_SIZE = 100
#how many words on each side of a word are used as its context
WINDOW = 5
#words that appear fewer times than this get no vector (too few examples to learn a good one)
MIN_COUNT = 2
#negative examples (random words) for every real (word, context) pair
NEGATIVE = 5
#passes over the corpus
EPOCHS = 5
#learning rate at the start, it goes down linearly to almost 0 at the end
LEARNING_RATE = 0.025
#very frequent words (men, women, cotton...) are randomly skipped: they appear everywhere, so they say little
SUBSAMPLE = 1e-3
#number of pairs updated at the same time
BATCH_SIZE = 1024
#fixed seed so training gives the same vectors every time
SEED = 42


class WordVectors:
    """
    The trained word vectors: one row of `vectors` per word of the vocabulary.
    """

    def __init__(self, words, vectors):
        self.words = words
        self.word_to_id = {w: i for i, w in enumerate(words)}
        self.vectors = vectors
        self.vector_size = vectors.shape[1]

    def __contains__(self, word):
        return word in self.word_to_id

    def __getitem__(self, word):
        return self.vectors[self.word_to_id[word]]

    def most_similar(self, word, topn=5):
        #cosine between the word and every other word
        unit_vectors = self.vectors / np.maximum(np.linalg.norm(self.vectors, axis=1, keepdims=True), 1e-12)
        similarities = unit_vectors @ unit_vectors[self.word_to_id[word]]
        best = [i for i in np.argsort(-similarities) if self.words[i] != word][:topn]
        return [(self.words[i], float(similarities[i])) for i in best]


def sigmoid(x):
    return 1 / (1 + np.exp(-np.clip(x, -10, 10)))


def make_pairs(docs, window, rng):
    """
    All the (word, context word) pairs of one epoch: words at distance <= window inside the same product.
    As in the original word2vec, closer words are used more often (dynamic window).
    :param docs: list of arrays of word ids, one per product
    :return: two arrays (centre words, context words)
    """
    ids = np.concatenate(docs)
    doc_of = np.repeat(np.arange(len(docs)), [len(d) for d in docs])
    centres, contexts = [], []
    for distance in range(1, window + 1):
        #pairs (i, i + distance) that don't cross from one product to the next
        same_doc = doc_of[:-distance] == doc_of[distance:]
        #a pair at this distance is kept with probability (window - distance + 1) / window
        keep = same_doc & (rng.random(len(same_doc)) < (window - distance + 1) / window)
        left, right = ids[:-distance][keep], ids[distance:][keep]
        #both directions: each word is the context of the other
        centres += [left, right]
        contexts += [right, left]
    return np.concatenate(centres), np.concatenate(contexts)


def train_word2vec(corpus, vector_size=VECTOR_SIZE, window=WINDOW, min_count=MIN_COUNT, negative=NEGATIVE, epochs=EPOCHS, seed=SEED):
    """
    Train word2vec (skip-gram with negative sampling) on our own products, one sentence per product.
    For every pair (word, context word) the model makes their vectors closer, and for negative
    random words it makes them further apart. Words that appear in similar contexts end up close.
    :param corpus: dataframe with the column 'all_tokens' (processed tokens of Part 1)
    :return: WordVectors with one vector per word that appears at least min_count times
    """
    rng = np.random.default_rng(seed)

    #vocabulary: words that appear at least min_count times
    counts = Counter(token for tokens in corpus["all_tokens"] for token in tokens)
    words = sorted(str(w) for w, c in counts.items() if c >= min_count)
    word_to_id = {w: i for i, w in enumerate(words)}
    freq = np.array([counts[w] for w in words], dtype=float)
    docs = [np.array([word_to_id[t] for t in tokens if t in word_to_id], dtype=np.int64) for tokens in corpus["all_tokens"]]

    #probability of keeping each word when subsampling, and of choosing it as a negative example (freq^0.75)
    share = freq / freq.sum()
    keep_prob = np.minimum(1, np.sqrt(SUBSAMPLE / share) + SUBSAMPLE / share)
    negative_cdf = np.cumsum(freq ** 0.75 / (freq ** 0.75).sum())

    #two vectors per word: as a centre word (the ones we keep) and as a context word
    w_in = ((rng.random((len(words), vector_size)) - 0.5) / vector_size).astype(np.float32)
    w_out = np.zeros((len(words), vector_size), dtype=np.float32)

    for epoch in range(epochs):
        kept_docs = [d[rng.random(len(d)) < keep_prob[d]] for d in docs]
        centres, contexts = make_pairs(kept_docs, window, rng)
        order = rng.permutation(len(centres))
        centres, contexts = centres[order], contexts[order]

        for start in range(0, len(centres), BATCH_SIZE):
            #learning rate goes down from LEARNING_RATE to almost 0 over all the training
            progress = (epoch + start / len(centres)) / epochs
            lr = np.float32(LEARNING_RATE * max(1 - progress, 0.0001))

            c = centres[start:start + BATCH_SIZE]
            o = contexts[start:start + BATCH_SIZE]
            n = np.minimum(np.searchsorted(negative_cdf, rng.random((len(c), negative))), len(words) - 1)

            v = w_in[c]          #(batch, size)
            u_pos = w_out[o]     #(batch, size)
            u_neg = w_out[n]     #(batch, negative, size)

            #error of the prediction: real pairs should give 1, negative pairs 0
            g_pos = sigmoid(np.sum(v * u_pos, axis=1)) - 1
            g_neg = sigmoid(np.einsum("bs,bns->bn", v, u_neg))

            grad_v = g_pos[:, None] * u_pos + np.einsum("bn,bns->bs", g_neg, u_neg)
            np.add.at(w_out, o, -lr * g_pos[:, None] * v)
            np.add.at(w_out, n.ravel(), -lr * (g_neg[:, :, None] * v[:, None, :]).reshape(-1, vector_size))
            np.add.at(w_in, c, -lr * grad_v)

        print(f"word2vec: epoch {epoch + 1}/{epochs} done")

    return WordVectors(words, w_in)


def save_word_vectors(wv, path):
    #save the vectors so the notebook doesn't have to train again (training takes a few minutes)
    np.savez(path, words=np.array(wv.words), vectors=wv.vectors)


def load_word_vectors(path):
    saved = np.load(path)
    return WordVectors(saved["words"].tolist(), saved["vectors"])


def text_vector(tokens, wv):
    """
    Vector of a text = average of the vectors of its words.
    Words without a vector (fewer than MIN_COUNT occurrences) are skipped.
    :param tokens: list of processed terms
    :param wv: output of train_word2vec
    :return: numpy vector, all zeros if no word has a vector
    """
    vectors = [wv[token] for token in tokens if token in wv]
    if not vectors:
        return np.zeros(wv.vector_size)
    return np.mean(vectors, axis=0)


def unit(vector):
    #divide by the length, so the dot product of two unit vectors is their cosine
    norm = np.linalg.norm(vector)
    return vector / norm if norm > 0 else vector


def create_word2vec_data(corpus, wv):
    """
    Precompute the (unit) vector of every product.
    :param corpus: dataframe with the columns 'pid' and 'all_tokens'
    :param wv: output of train_word2vec
    :return: dict with the word vectors and pid -> unit document vector
    """
    doc_vectors = {pid: unit(text_vector(tokens, wv)) for pid, tokens in zip(corpus["pid"], corpus["all_tokens"])}
    return {"wv": wv, "doc_vectors": doc_vectors}


def rank_word2vec_cosine(query_terms, docs, w2v_data):
    """
    Rank documents with word2vec + cosine similarity.
    score = cos(query vector, document vector), both being averages of word vectors
    :param query_terms: list of processed query terms
    :param docs: pids to rank (output of conjunctive_search)
    :param w2v_data: output of create_word2vec_data
    :return: list of (pid, score) sorted from best to worst
    """
    query_vector = unit(text_vector(query_terms, w2v_data["wv"]))
    scores = [(pid, float(np.dot(query_vector, w2v_data["doc_vectors"][pid]))) for pid in docs]
    return sort_scores(scores)


def search_word2vec(query, index, w2v_data, k=20):
    """
    Full search: preprocess the query, keep the documents with ALL the terms and rank them with word2vec.
    :param query: query text as written by the user
    :param k: number of results to return (None = all)
    :return: list of (pid, score) with the top k results
    """
    query_terms = preprocess_text(query)
    if not query_terms:
        return []

    docs = conjunctive_search(query_terms, index)
    ranked = rank_word2vec_cosine(query_terms, docs, w2v_data)
    if k is None:
        return ranked
    return ranked[:k]
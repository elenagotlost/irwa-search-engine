"""
Text and field pre-processing for the IRWA fashion-products search engine (Part 1).

The module turns each raw product record into a clean, search-ready record with:

* the original display fields kept untouched (pid, title, description, brand, ...,
  url) so that later parts can return them to the user, and
* token lists for every searchable text field (title, description, product
  details, brand) plus a combined ``all_tokens`` field, and
* parsed numeric / boolean fields (prices, discount, rating, stock) that are
  NOT indexed as text but kept as typed attributes for filtering and ranking.

All functions are pure (no global state is modified) so they can be reused for
queries in Parts 2-4: a query must go through exactly the same
``preprocess_text`` pipeline as the documents, otherwise terms will not match.
"""

from __future__ import annotations

import re
import unicodedata
from functools import lru_cache
from typing import Any, Dict, Iterable, List, Optional

import numpy as np
import pandas as pd
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer
from nltk.tokenize import word_tokenize

# --------------------------------------------------------------------------------------
# Resources
# --------------------------------------------------------------------------------------

STEMMER = PorterStemmer()

# NLTK English stop-word list. We deliberately do NOT add "men"/"women"/"full" etc.:
# gender and sleeve words are among the most discriminative terms in the validation
# queries ("women full sleeve sweatshirt cotton", "men slim jeans blue").
STOP_WORDS = set(stopwords.words("english"))

# Domain phrases that appear spelled in several ways. They are normalised to one form
# BEFORE punctuation removal so that "T-Shirt", "t shirt", "tshirt" and "tee" match.
PHRASE_NORMALISATION = [
    (r"\bt[\s\-]?shirts?\b", "tshirt"),
    (r"\btees?\b", "tshirt"),
    (r"\bsweat[\s\-]shirts?\b", "sweatshirt"),
    (r"\bhood(ie|y)s?\b", "hoodie"),
    (r"\bjean\b", "jeans"),
]

# Glued compounds found in product_details values (e.g. Fit: "Slimfit").
# They are split so that the query term "slim" matches them.
COMPOUND_SPLITS = {
    "slimfit": "slim fit",
    "regularfit": "regular fit",
    "skinnyfit": "skinny fit",
    "relaxedfit": "relaxed fit",
    "fullsleeve": "full sleeve",
    "halfsleeve": "half sleeve",
    "roundneck": "round neck",
    "vneck": "v neck",
}

# product_details keys whose values carry no topical information (codes, washing
# instructions, packaging, provenance). Their values are excluded from the text.
DETAIL_KEYS_TO_DROP = {
    "Style Code",
    "Model Name",
    "Fabric Care",
    "Sales Package",
    "Number of Contents in Sales Package",
    "Pack of",
    "Country of Origin",
    "Other Details",
    "Net Quantity",
    "Width",
    "Length",
}

# Fields every result must expose to the user (assignment, Part 1 point 2).
OUTPUT_FIELDS = [
    "pid", "title", "description", "brand", "category", "sub_category",
    "product_details", "seller", "out_of_stock", "selling_price", "discount",
    "actual_price", "average_rating", "url",
]


# --------------------------------------------------------------------------------------
# Text pipeline
# --------------------------------------------------------------------------------------

def normalise_text(text: Optional[str]) -> str:
    """Lower-case, strip accents and unify domain spellings of a raw string.

    Steps:
      1. ``None``/NaN become an empty string.
      2. Unicode NFKD + ASCII folding removes accents and odd symbols ("Café" -> "cafe").
      3. Lower-casing.
      4. Domain phrase normalisation (``PHRASE_NORMALISATION``), e.g. "t-shirt" -> "tshirt".
      5. Apostrophes are dropped so "men's" -> "mens" (stemmed later to "men").
      6. Every other non-alphanumeric character becomes a space. This both removes
         punctuation and separates words glued by punctuation in the raw data
         ("rich look.Designed for Comfort,Skin" -> "rich look designed for comfort skin").
      7. Glued compounds are split (``COMPOUND_SPLITS``).

    :param text: raw text (may be None).
    :return: normalised string with single spaces.
    """
    if text is None or (isinstance(text, float) and np.isnan(text)):
        return ""
    text = unicodedata.normalize("NFKD", str(text)).encode("ascii", "ignore").decode("ascii")
    text = text.lower()
    for pattern, replacement in PHRASE_NORMALISATION:
        text = re.sub(pattern, replacement, text)
    text = re.sub(r"['`]", "", text)
    text = re.sub(r"[^a-z0-9]+", " ", text)
    tokens = [COMPOUND_SPLITS.get(t, t) for t in text.split()]
    return " ".join(tokens)


def tokenize(text: str) -> List[str]:
    """Split a normalised string into tokens with NLTK's ``word_tokenize``.

    Punctuation is already removed by :func:`normalise_text`, so this mainly splits on
    whitespace, but using the NLTK tokenizer keeps the step explicit and robust.
    """
    return word_tokenize(text) if text else []


def remove_stopwords(tokens: Iterable[str]) -> List[str]:
    """Remove English stop words, single characters and pure numbers.

    Pure numbers ("100" from "100% cotton", "2" from "pack of 2") are removed because
    prices/percentages/pack sizes are handled as typed numeric fields, and as text they
    match almost randomly. Alphanumeric tokens such as "4xl" or "s21" are kept.
    """
    return [
        t for t in tokens
        if t not in STOP_WORDS and len(t) > 1 and not t.isdigit()
    ]


@lru_cache(maxsize=200_000)
def stem(token: str) -> str:
    """Porter-stem one token (cached: the vocabulary is small but repeated a lot)."""
    return STEMMER.stem(token)


def preprocess_text(text: Optional[str], use_stemming: bool = True) -> List[str]:
    """Full pipeline used for BOTH documents and queries.

    normalise -> tokenize -> remove stop words / numbers -> stem.

    >>> preprocess_text("Yorker trackpants made from 100% rich combed cotton.Designed for Comfort")
    ['yorker', 'trackpant', 'made', 'rich', 'comb', 'cotton', 'design', 'comfort']
    >>> preprocess_text("women full sleeve sweatshirt cotton")
    ['women', 'full', 'sleev', 'sweatshirt', 'cotton']

    :param text: raw text.
    :param use_stemming: set False to inspect the un-stemmed tokens (used in the EDA).
    :return: list of processed terms.
    """
    tokens = remove_stopwords(tokenize(normalise_text(text)))
    return [stem(t) for t in tokens] if use_stemming else tokens


# --------------------------------------------------------------------------------------
# Structured fields
# --------------------------------------------------------------------------------------

def flatten_product_details(details: Any) -> Dict[str, str]:
    """Turn the raw ``product_details`` list of one-key dicts into a single dict.

    ``[{"Fabric": "Cotton"}, {"Color": "Blue"}]`` -> ``{"Fabric": "Cotton", "Color": "Blue"}``
    """
    if isinstance(details, dict):
        return dict(details)
    merged: Dict[str, str] = {}
    if isinstance(details, list):
        for item in details:
            if isinstance(item, dict):
                merged.update(item)
    return merged


def product_details_to_text(details: Dict[str, str]) -> str:
    """Build the searchable text of the product details.

    * Values of non-informative keys (``DETAIL_KEYS_TO_DROP``) are ignored.
    * Yes/No attributes are turned into the attribute name when "Yes"
      ({"Hooded": "Yes"} -> "hooded"); "No" is dropped, since "no" carries no meaning
      without its key.
    * All other values are kept (Fabric, Sleeve, Fit, Color, Ideal For, Pattern, ...).
      Keys themselves are not indexed: "Fabric" or "Pattern" appear in almost every
      product and would only add noise.
    * Repeated values are kept once: many products state the same value under two keys
      ("Type: Round Neck" and "Neck Type: Round Neck", "Color" and "Brand Color"), which
      would otherwise double the term frequency for no reason.
    """
    parts: List[str] = []
    seen = set()
    for key, value in details.items():
        if key in DETAIL_KEYS_TO_DROP or value is None:
            continue
        value = str(value).strip()
        if value.lower() == "yes":
            value = key
        elif value.lower() in {"no", "na", "n/a", ""}:
            continue
        if value.lower() not in seen:
            seen.add(value.lower())
            parts.append(value)
    return " ".join(parts)


def normalise_keyword(value: Optional[str]) -> str:
    """Normalise a categorical value (brand, seller, category) as ONE keyword.

    These fields are used for exact-match filtering/faceting, so they are lower-cased
    and whitespace-collapsed but not split or stemmed ("Clothing and Accessories" stays
    one value). Empty strings become "".
    """
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return ""
    return re.sub(r"\s+", " ", str(value)).strip().lower()


def parse_number(value: Any) -> float:
    """Parse "2,999" / "69% off" / "3.9" / "" into a float (NaN when missing)."""
    if value is None:
        return np.nan
    if isinstance(value, (int, float)):
        return float(value)
    match = re.search(r"\d+(?:\.\d+)?", str(value).replace(",", ""))
    return float(match.group()) if match else np.nan


def parse_numeric_fields(df: pd.DataFrame) -> pd.DataFrame:
    """Add typed numeric columns (suffix ``_num``) next to the raw string columns.

    * ``selling_price_num``, ``actual_price_num``: float rupees.
    * ``discount_num``: percentage. When the raw value is empty it is recomputed from
      the two prices; when there is no list price at all, actual = selling price and
      the discount is 0 (``price_imputed`` marks those rows).
    * ``average_rating_num``: float in [1, 5], NaN when the product has no rating. We do
      NOT impute 0 (that would mean "rated terribly") nor the mean (that would invent
      information); ``has_rating`` lets the ranker treat unrated products explicitly.
    * ``out_of_stock``: kept as bool.
    """
    out = df.copy()
    out["selling_price_num"] = out["selling_price"].map(parse_number)
    out["actual_price_num"] = out["actual_price"].map(parse_number)
    out["discount_num"] = out["discount"].map(parse_number)

    # Products with an empty actual_price also have an empty discount: the shop shows
    # only one price when nothing is discounted. We therefore assume
    # actual_price = selling_price and discount = 0, and flag the rows.
    no_list_price = out["actual_price_num"].isna() & out["selling_price_num"].notna()
    out["price_imputed"] = no_list_price
    out.loc[no_list_price, "actual_price_num"] = out.loc[no_list_price, "selling_price_num"]

    missing = out["discount_num"].isna() & out["actual_price_num"].gt(0) & out["selling_price_num"].notna()
    out.loc[missing, "discount_num"] = (
        (1 - out.loc[missing, "selling_price_num"] / out.loc[missing, "actual_price_num"]) * 100
    ).round()

    out["average_rating_num"] = out["average_rating"].map(parse_number)
    out["has_rating"] = out["average_rating_num"].notna()
    out["out_of_stock"] = out["out_of_stock"].astype(bool)
    return out


# --------------------------------------------------------------------------------------
# Corpus level
# --------------------------------------------------------------------------------------

def load_raw_corpus(path: str) -> pd.DataFrame:
    """Load the JSON dataset into a DataFrame (one row per product, ``pid`` kept)."""
    return pd.read_json(path)


def preprocess_corpus(df: pd.DataFrame, use_stemming: bool = True) -> pd.DataFrame:
    """Pre-process the whole corpus.

    Returned columns:
      * all ``OUTPUT_FIELDS`` in their original form (``product_details`` as a flat dict),
      * ``title_tokens``, ``description_tokens``, ``details_tokens``, ``brand_tokens``:
        processed terms per field (for a fielded index / field weighting, e.g. BM25F),
      * ``all_tokens``: title + description + details + brand (for a single index),
      * ``brand_kw``, ``seller_kw``, ``category_kw``, ``sub_category_kw``: normalised
        keywords for filtering,
      * typed numeric columns from :func:`parse_numeric_fields`.

    :param df: raw DataFrame from :func:`load_raw_corpus`.
    :param use_stemming: forwarded to :func:`preprocess_text`.
    """
    out = parse_numeric_fields(df)
    out["product_details"] = out["product_details"].map(flatten_product_details)

    out["title_tokens"] = out["title"].map(lambda t: preprocess_text(t, use_stemming))
    out["description_tokens"] = out["description"].map(lambda t: preprocess_text(t, use_stemming))
    out["details_tokens"] = out["product_details"].map(
        lambda d: preprocess_text(product_details_to_text(d), use_stemming)
    )
    out["brand_tokens"] = out["brand"].map(lambda t: preprocess_text(t, use_stemming))
    out["all_tokens"] = (
        out["title_tokens"] + out["description_tokens"] + out["details_tokens"] + out["brand_tokens"]
    )

    for col in ["brand", "seller", "category", "sub_category"]:
        out[f"{col}_kw"] = out[col].map(normalise_keyword)

    keep = (
        OUTPUT_FIELDS
        + ["title_tokens", "description_tokens", "details_tokens", "brand_tokens", "all_tokens"]
        + ["brand_kw", "seller_kw", "category_kw", "sub_category_kw"]
        + ["selling_price_num", "actual_price_num", "discount_num", "average_rating_num", "has_rating",
           "price_imputed"]
    )
    return out[keep]

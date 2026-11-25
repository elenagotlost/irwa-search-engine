"""
Query understanding for the RAG (Part 4, improvement 2).

Users write things like "women cotton kurta under 500" or "running shoes rated 4+ stars".
Our preprocessing removes stop words ("under", "above") and numbers, so the AND search only sees
"kurta" and the price limit is lost. Words like "rs", "rating" or "cheap" are worse: they become
AND terms that almost no product contains, so the search returns nothing.

parse_constraints() finds these limits with regular expressions, returns them as numbers the RAG can
check against each product, and returns the query without them (search_text) for the AND search.
"""
import re
from dataclasses import dataclass, field
from typing import List, Optional

#a price: optional currency before or after the number ("rs 500", "₹500", "500 rs", "1,299")
_CUR = r"(?:rs\.?|inr|₹)"
_NUM = r"(\d[\d,]*(?:\.\d+)?)"
_PRICE = rf"(?:{_CUR}\s*)?{_NUM}(?:\s*(?:{_CUR}|rupees|/-))?"

#the rating patterns go first: "above 4 stars" must not be read as "price above 4"
_RATING_PATTERNS = [
    #"4+ stars", "at least 4 stars", "4 stars and above", "4 star rating"
    re.compile(r"(?:(?:above|over|at least|more than|min(?:imum)?)\s+)?(\d(?:\.\d)?)\s*\+?\s*(?:stars?|\*)"
               r"(?:\s+(?:and|or)\s+(?:above|up|more|higher|better))?(?:\s+ratings?)?"),
    #"rating above 4", "rated 4 or more", "rating of at least 4.2", "rating 4+"
    re.compile(r"(?:ratings?|rated)\s+(?:of\s+|is\s+)?(?:(?:above|over|at least|more than|min(?:imum)?|>=?)\s*)?"
               r"(\d(?:\.\d)?)\s*\+?(?:\s+(?:stars?|(?:and|or)\s+(?:above|up|more|higher|better)))*"),
]
_BETWEEN = re.compile(rf"(?:between|from)\s+{_PRICE}\s*(?:and|to|-)\s*{_PRICE}")
_RANGE = re.compile(rf"{_CUR}\s*{_NUM}\s*(?:-|to)\s*{_CUR}?\s*{_NUM}")
#"500-1000" with no currency: only numbers of 2+ digits, so "pack of 2-3" is not a price
_BARE_RANGE = re.compile(r"\b(\d{2,}[\d,]*)\s*-\s*(\d{2,}[\d,]*)\b")
_MAX_PRICE = re.compile(rf"(?:under|below|less than|cheaper than|up\s?to|within|max(?:imum)?|at most|not more than|<=?)\s*{_PRICE}")
_MIN_PRICE = re.compile(rf"(?:above|over|more than|at least|min(?:imum)?|>=?)\s*{_PRICE}")
#a bare price with a currency and no word before it ("kurta rs 500") is read as a maximum
_BARE_PRICE = re.compile(rf"(?:{_CUR}\s*{_NUM}|{_NUM}\s*(?:{_CUR}|rupees|/-))")

_CHEAP = re.compile(r"\b(?:cheap(?:est|er)?|budget|affordable|inexpensive|low(?:est)? (?:price|cost)|economical)\b")
_TOP_RATED = re.compile(r"\b(?:(?:top|best|highly|well|high)[\s-]rated|best reviewed|good (?:rating|reviews?)|highest rat(?:ed|ing))\b")
#leftover words that only describe the constraint and would break the AND search
_LEFTOVER = re.compile(r"\b(?:price[ds]?|priced|costing|cost|rupees|rs|inr|ratings?|rated|stars?|for|with|and above|or more)\b")


@dataclass
class QueryConstraints:
    """Limits found in the query. None means the user did not ask for that limit."""
    original: str
    search_text: str
    max_price: Optional[float] = None
    min_price: Optional[float] = None
    min_rating: Optional[float] = None
    prefer_cheap: bool = False
    prefer_rating: bool = False
    found: List[str] = field(default_factory=list)  #the pieces of text we understood, to show the user

    @property
    def has_hard_limits(self):
        return any(v is not None for v in (self.max_price, self.min_price, self.min_rating))

    def describe(self):
        """Short text with the limits, e.g. 'price ≤ Rs. 500, rating ≥ 4.0'."""
        parts = []
        if self.min_price is not None and self.max_price is not None:
            parts.append(f"price Rs. {self.min_price:,.0f}–{self.max_price:,.0f}")
        elif self.max_price is not None:
            parts.append(f"price ≤ Rs. {self.max_price:,.0f}")
        elif self.min_price is not None:
            parts.append(f"price ≥ Rs. {self.min_price:,.0f}")
        if self.min_rating is not None:
            parts.append(f"rating ≥ {self.min_rating:.1f}")
        if self.prefer_cheap:
            parts.append("prefers low price")
        if self.prefer_rating:
            parts.append("prefers high rating")
        return ", ".join(parts)

    def check(self, price, rating):
        """
        Which hard limits a product breaks.
        A product with no price or no rating breaks the limit on that field: we can't promise it fits.
        :return: list of short reasons, empty if the product fits
        """
        broken = []
        if self.max_price is not None and (price is None or price > self.max_price):
            broken.append("price")
        if self.min_price is not None and (price is None or price < self.min_price):
            broken.append("price")
        if self.min_rating is not None and (rating is None or rating < self.min_rating):
            broken.append("rating")
        return broken


def _to_float(text):
    return float(text.replace(",", ""))


def parse_constraints(query: str) -> QueryConstraints:
    """
    Find price limits, a minimum rating and cheap / top-rated preferences in a query.
    :param query: query as written by the user
    :return: QueryConstraints, with search_text = the query without the constraint words
    """
    text = (query or "").lower()
    c = QueryConstraints(original=query or "", search_text="")

    def cut(match):
        #replace the matched text with spaces so the other patterns can't use it again
        nonlocal text
        c.found.append(match.group(0).strip())
        text = text[:match.start()] + " " * (match.end() - match.start()) + text[match.end():]

    for pattern in _RATING_PATTERNS:
        m = pattern.search(text)
        if m and c.min_rating is None:
            value = float(m.group(1))
            if 0 < value <= 5:
                c.min_rating = value
                cut(m)

    m = _BETWEEN.search(text) or _RANGE.search(text) or _BARE_RANGE.search(text)
    if m:
        low, high = sorted((_to_float(m.group(1)), _to_float(m.group(2))))
        c.min_price, c.max_price = low, high
        cut(m)
    else:
        m = _MAX_PRICE.search(text)
        if m:
            c.max_price = _to_float(m.group(1))
            cut(m)
        m = _MIN_PRICE.search(text)
        if m:
            c.min_price = _to_float(m.group(1))
            cut(m)
        if c.max_price is None and c.min_price is None:
            m = _BARE_PRICE.search(text)
            if m:
                c.max_price = _to_float(m.group(1) or m.group(2))
                cut(m)

    m = _CHEAP.search(text)
    if m:
        c.prefer_cheap = True
        cut(m)
    m = _TOP_RATED.search(text)
    if m:
        c.prefer_rating = True
        cut(m)

    #only clean the leftovers when we found something, otherwise the query is left exactly as it was
    if c.found:
        text = _LEFTOVER.sub(" ", text)
        c.search_text = re.sub(r"\s+", " ", text).strip()
    else:
        c.search_text = (query or "").strip()
    return c

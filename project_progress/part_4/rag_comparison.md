# Baseline vs improved RAG

Model: `openai/gpt-oss-20b`. Generated 2026-11-26 10:11.

## Summary

```
          queries  recommended  valid_pid  fits_limits  said_no_match  empty_or_failed  mean_seconds  mean_prompt_tokens
system                                                                                                                  
baseline       12            3          3            3              4                0          2.16               806.5
improved       12           10         10           10              2                0          7.53              1599.5
```

## `men cotton polo tshirt`

Limits understood: none · search text for improved: `men cotton polo tshirt`

**Baseline** (1,213 results, valid PID: True, fits limits: True)

```
- Best Product: TSHFUGNWKWGPZ32S Solid Men Polo Neck Black T-Shirt  
- Why: This polo is a classic solid black, making it highly versatile for both casual and semi‑formal settings. The solid color keeps it simple and timeless, while the polo style ensures a polished look without the need for extra layering. It’s an ideal choice for a wardrobe staple that can be worn in office, weekend outings, or relaxed events.  
- Alternative: TSHFZQBGBQGXVRHJ Printed Men Polo Neck Grey T-Shirt (a neutral grey version for a slightly more relaxed vibe).
```

**Improved** (1,213 results, status `ok`, valid PID: True, fits limits: True)

```
- Best Product: [1] TSHFZQBG3J5GREG2 Printed Men Polo Neck Black T-Shirt
- Why: Pure Cotton, Polo Neck, Rs. 499, rating 4.7/5
- Alternative: [2] TSHFZQBGBQGXVRHJ Printed Men Polo Neck Grey T-Shirt - Pure Cotton, Polo Neck, Rs. 449, rating 4.7/5
(1,182 of 1,213 matching products are in stock; prices Rs. 230–Rs. 3,672; 320 rated 4+)
```

## `women cotton kurta`

Limits understood: none · search text for improved: `women cotton kurta`

**Baseline** (358 results, valid PID: True, fits limits: True)

```
- Best Product: KTAFWG3KHPEVYFRG Women Solid Pure Cotton Straight Kurta (Maroon)  
- Why: This kurta is made from 100 % pure cotton, ensuring breathability and comfort for everyday wear. The straight cut is classic and versatile, suitable for casual or semi‑formal occasions. The solid maroon color is a neutral, easy‑to‑mix hue that pairs well with a variety of accessories. Overall, it offers high material quality, a timeless style, and a reasonable price point for a solid cotton kurta.  
- Alternative: KTAFWG3KMZYPJ7NJ Women Solid Pure Cotton Straight Kurta (Green)
```

**Improved** (358 results, status `ok`, valid PID: True, fits limits: True)

```
- Best Product: [9] KTAFWG3KHPEVYFRG Women Solid Pure Cotton Straight Kurta  (Maroon)
- Why: Pure Cotton, 4.7/5 rating, Rs. 699
- Alternative: [10] KTAFWG3KMZYPJ7NJ Women Solid Pure Cotton Straight Kurta  (Green) - Pure Cotton, 4.7/5 rating, Rs. 699
(350 of 358 matching products are in stock; prices Rs. 390–Rs. 1,734; 93 rated 4+)
```

## `men hooded sweatshirt`

Limits understood: none · search text for improved: `men hooded sweatshirt`

**Baseline** (323 results, valid PID: None, fits limits: None)

```
There are no good products that fit the request based on the retrieved results.
```

**Improved** (323 results, status `ok`, valid PID: True, fits limits: True)

```
- Best Product: [1] SWSFJE3V7A8FHGNG Sleeveless Printed Men Sweatshirt
- Why: Lowest price Rs. 499 and highest rating 5.0/5 among hooded sweatshirts
- Alternative: [2] SWSFYFFFMWQMAPJJ Full Sleeve Printed Men Sweatshirt - Next lowest price Rs. 649 but lower rating 3.2/5
(295 of 323 matching products are in stock; prices Rs. 254–Rs. 4,500; 107 rated 4+)
```

## `men running shoes`

Limits understood: none · search text for improved: `men running shoes`

**Baseline** (37 results, valid PID: True, fits limits: True)

```
- Best Product: PID: SHOFTZFQQYKC8HY6 Running Shoes For Men  (Yellow)  
- Why: This shoe is a straightforward, all‑purpose running shoe that is likely to be competitively priced and suitable for everyday training. Its single‑color design keeps options simple while still offering the comfort and fit needed for men’s running shoes.  
- Alternative: PID: SHOFTZFPNCU4VWHK Running Shoes For Men  (Black)
```

**Improved** (37 results, status `ok`, valid PID: True, fits limits: True)

```
- Best Product: [1] SHOFTZFQQYKC8HY6 Running Shoes For Men  (Yellow)
- Why: Lowest price Rs.341 and rating 4.1/5 among men running shoes.
- Alternative: [2] SHOFTZFPNCU4VWHK Running Shoes For Men  (Black) - Same brand and rating, slightly higher price Rs.379.
(34 of 37 matching products are in stock; prices Rs. 197–Rs. 1,790; 14 rated 4+)
```

## `women blue denim jacket`

Limits understood: none · search text for improved: `women blue denim jacket`

**Baseline** (27 results, valid PID: None, fits limits: None)

```
"There are no good products that fit the request based on the retrieved results."
```

**Improved** (27 results, status `ok`, valid PID: True, fits limits: True)

```
- Best Product: [5] JCKFVEUDNF3J7CWV Full Sleeve Solid Women Jacket
- Why: Blue denim jacket with 4.2/5 rating and Rs. 1,199 price.
- Alternative: [6] JCKFVEUDBT4KKSXR Full Sleeve Solid Women Jacket - Dark blue denim jacket, same price but lower rating.
(24 of 27 matching products are in stock; prices Rs. 249–Rs. 2,144; 11 rated 4+)
```

## `women cotton kurta under 500`

Limits understood: price ≤ Rs. 500 · search text for improved: `women cotton kurta`

**Baseline** (358 results, valid PID: None, fits limits: None)

```
"There are no good products that fit the request based on the retrieved results."
```

**Improved** (358 results, status `ok`, valid PID: True, fits limits: True)

```
- Best Product: [3] KTAFZFX7HTMGQCG6 Women Solid Cotton Blend Straight Kurta  (Black)
- Why: Price Rs. 390 and rating 5.0/5 for a cotton blend straight kurta
- Alternative: [7] KTAFZFFP54CXBCHY Women Striped Pure Cotton Straight Kurta  (Green) - Price Rs. 495 and rating 4.1/5 for a pure cotton straight kurta
(44 of 358 matching products are in stock and fit price ≤ Rs. 500; prices Rs. 390–Rs. 499; 27 rated 4+)
```

## `men running shoes rating above 4`

Limits understood: rating ≥ 4.0 · search text for improved: `men running shoes`

**Baseline** (0 results, valid PID: None, fits limits: None)

```
(no results, RAG not called)
```

**Improved** (37 results, status `ok`, valid PID: True, fits limits: True)

```
- Best Product: [9] SHOEYF5UH4GPCETN Running Shoes For Men  (Green, Blue)
- Why: Rating 4.3/5 meets the ≥4.0 requirement and price Rs. 990 is lower than other 4.3/5 options.
- Alternative: [3] SHOESS9ZEZ6TEQUJ Running Shoes For Men  (Multicolor) - Also rating 4.3/5 but higher price Rs. 1,440.
(14 of 37 matching products are in stock and fit rating ≥ 4.0; prices Rs. 249–Rs. 1,790; 14 rated 4+)
```

## `cheap black jeans for women`

Limits understood: prefers low price · search text for improved: `black jeans women`

**Baseline** (0 results, valid PID: None, fits limits: None)

```
(no results, RAG not called)
```

**Improved** (337 results, status `ok`, valid PID: True, fits limits: True)

```
- Best Product: [1] JEAFJM2PHHPFTAH8 Slim Women Black Jeans
- Why: Lowest price Rs.545 and suitable for women, black color, cotton lycra blend.
- Alternative: [2] JEAFF3TGFMW6KMBG Regular Women Black Jeans - Next cheapest Rs.649, denim fabric, also black for women.
(302 of 337 matching products are in stock; prices Rs. 199–Rs. 4,296; 155 rated 4+)
```

## `top rated men hooded sweatshirt`

Limits understood: prefers high rating · search text for improved: `men hooded sweatshirt`

**Baseline** (0 results, valid PID: None, fits limits: None)

```
(no results, RAG not called)
```

**Improved** (323 results, status `ok`, valid PID: True, fits limits: True)

```
- Best Product: [1] SWSFJE3V7A8FHGNG Sleeveless Printed Men Sweatshirt
- Why: Highest rating 5.0/5 and hooded sweatshirt for men.
- Alternative: [2] SWSFZUEBYU5DM9CH Full Sleeve Printed Men Sweatshirt - Second highest rating 4.6/5, also a hooded men’s sweatshirt.
(295 of 323 matching products are in stock; prices Rs. 254–Rs. 4,500; 107 rated 4+)
```

## `men polo tshirt between 300 and 600 rs`

Limits understood: price Rs. 300–600 · search text for improved: `men polo tshirt`

**Baseline** (0 results, valid PID: None, fits limits: None)

```
(no results, RAG not called)
```

**Improved** (1,440 results, status `ok`, valid PID: True, fits limits: True)

```
- Best Product: [3] TSHFZ67FFFJ2S4CQ Solid Men Polo Neck Grey T-Shirt
- Why: Solid Men Polo Neck Grey T-Shirt priced at Rs. 339 with a rating of 4.3/5 fits the 300–600 Rs budget and offers a solid fit.
- Alternative: [1] TSHFZQBG3J5GREG2 Printed Men Polo Neck Black T-Shirt - Printed Men Polo Neck Black T-Shirt costs Rs. 499 and has a higher rating of 4.7/5, but is pricier than the best match.
(680 of 1,440 matching products are in stock and fit price Rs. 300–600; prices Rs. 300–Rs. 600; 250 rated 4+)
```

## `men hooded sweatshirt under 100`

Limits understood: price ≤ Rs. 100 · search text for improved: `men hooded sweatshirt`

**Baseline** (323 results, valid PID: None, fits limits: None)

```
"There are no good products that fit the request based on the retrieved results."
```

**Improved** (323 results, status `no_match`, valid PID: None, fits limits: None)

```
None of the 323 products that match your words fits price ≤ Rs. 100. Closest option: Sleeveless Printed Men Sweatshirt (SWSFJE3V7A8FHGNG) - the cheapest is Rs. 499. Try relaxing the limit.
```

## `women denim jacket 5 stars under 300`

Limits understood: price ≤ Rs. 300, rating ≥ 5.0 · search text for improved: `women denim jacket`

**Baseline** (0 results, valid PID: None, fits limits: None)

```
(no results, RAG not called)
```

**Improved** (82 results, status `no_match`, valid PID: None, fits limits: None)

```
None of the 82 products that match your words fits price ≤ Rs. 300, rating ≥ 5.0. Closest option: Full Sleeve Washed Women Denim Jacket (JCKFEEE99F4ZHMEE) - the cheapest is Rs. 943. Try relaxing the limit.
```

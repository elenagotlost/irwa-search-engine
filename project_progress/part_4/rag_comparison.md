# Baseline vs improved RAG

Model: `openai/gpt-oss-20b`. Generated 2026-11-25 11:26.

## Summary

```
          queries  recommended  valid_pid  fits_limits  said_no_match  mean_seconds  mean_prompt_tokens
system                                                                                                 
baseline       12            4          4            4              3          2.56               806.5
improved       12            7          7            7              2         14.39              1585.5
```

## `men cotton polo tshirt`

Limits understood: none · search text for improved: `men cotton polo tshirt`

**Baseline** (1,213 results, valid PID: True, fits limits: True)

```
- Best Product: **TSHFUGNWKWGPZ32S Solid Men Polo Neck Black T-Shirt**  
- Why: This shirt is a classic, solid‑color polo that works well for a wide range of occasions. It’s a neutral black that pairs easily with almost any outfit, making it a versatile staple. The title indicates a solid design, which tends to be more formal or office‑ready, while the "Men Polo Neck" ensures the fit is tailored for a masculine silhouette.  

- Alternative (optional): **TSHFZQBG3J5GREG2 Printed Men Polo Neck Black T-Shirt** – if you prefer a subtle pattern or a little visual interest, this printed version offers the same solid black base with a discreet design.
```

**Improved** (1,213 results, status `ok`, valid PID: True, fits limits: True)

```
- Best Product: [2] TSHFZQBGBQGXVRHJ Printed Men Polo Neck Grey T-Shirt
- Why: Pure Cotton Polo Neck, price Rs. 449, rating 4.7/5
- Alternative: [1] TSHFZQBG3J5GREG2 Printed Men Polo Neck Black T-Shirt - Pure Cotton Polo Neck, price Rs. 499, rating 4.7/5, slightly higher price
(1,182 of 1,213 matching products are in stock; prices Rs. 230–Rs. 3,672; 320 rated 4+)
```

## `women cotton kurta`

Limits understood: none · search text for improved: `women cotton kurta`

**Baseline** (358 results, valid PID: True, fits limits: True)

```
- Best Product: KTAFWG3KHPEVYFRG Women Solid Pure Cotton Straight Kurta (Maroon)  
- Why: This kurta is made from 100% pure cotton, giving it a natural feel, breathability, and durability that blend fabrics can’t match. The straight cut offers a classic, flattering fit for everyday wear, and the maroon color is versatile enough to pair with a variety of bottoms or accessories.  
- Alternative: KTAFWG3KMZYPJ7NJ Women Solid Pure Cotton Straight Kurta (Green)
```

**Improved** (358 results, status `ok`, valid PID: True, fits limits: True)

```
- Best Product: [9] KTAFWG3KHPEVYFRG Women Solid Pure Cotton Straight Kurta  (Maroon)
- Why: Pure Cotton, Rs.699, 4.7/5 rating, matches the user’s request for a women cotton kurta.
- Alternative: [10] KTAFWG3KMZYPJ7NJ Women Solid Pure Cotton Straight Kurta  (Green) - Also Pure Cotton, Rs.699, 4.7/5 rating, but in Green instead of Maroon.
(350 of 358 matching products are in stock; prices Rs. 390–Rs. 1,734; 93 rated 4+)
```

## `men hooded sweatshirt`

Limits understood: none · search text for improved: `men hooded sweatshirt`

**Baseline** (323 results, valid PID: None, fits limits: None)

```
"There are no good products that fit the request based on the retrieved results."
```

**Improved** (323 results, status `unparsed`, valid PID: None, fits limits: None)

```
(295 of 323 matching products are in stock; prices Rs. 254–Rs. 4,500; 107 rated 4+)
```

## `men running shoes`

Limits understood: none · search text for improved: `men running shoes`

**Baseline** (37 results, valid PID: True, fits limits: True)

```
- Best Product: SHOFN3EJVGC9VXYT RS-7200 Running Shoes For Men (Navy)  
- Why: This is a dedicated RS‑series model, which typically means enhanced cushioning, stability, and breathable materials designed specifically for running. The Navy color is a versatile choice that pairs well with most athletic outfits.  
- Alternative: SHOFN3EJHXHGSGUC RS-7250 Running Shoes For Men (Black)
```

**Improved** (37 results, status `unparsed`, valid PID: None, fits limits: None)

```
(34 of 37 matching products are in stock; prices Rs. 197–Rs. 1,790; 14 rated 4+)
```

## `women blue denim jacket`

Limits understood: none · search text for improved: `women blue denim jacket`

**Baseline** (27 results, valid PID: True, fits limits: True)

```
- Best Product: JCKFWC5YGQENYT6B Full Sleeve Solid Women Denim Jacket  
- Why: This jacket is a classic blue denim style with a full‑sleeve cut that fits most women comfortably. It’s a solid denim fabric, which gives a versatile, casual look while providing good durability and a flattering silhouette. The price point (not provided here but typical for this model) balances quality and affordability.  
- Alternative: JCKFV7V7ZQ3PUSFF Full Sleeve Washed Women Denim Riding Jacket – another blue denim option that features a slightly relaxed, riding‑jacket cut if you prefer a more casual, roomy fit.
```

**Improved** (27 results, status `ok`, valid PID: True, fits limits: True)

```
- Best Product: [5] JCKFVEUDNF3J7CWV Full Sleeve Solid Women Jacket
- Why: Best match: blue denim jacket for women with highest rating 4.2/5 and lowest price Rs. 1,199.
- Alternative: [7] JCKFZ33GHPEXHFUZ Full Sleeve Solid Women Jacket - Alternative: blue denim jacket with lower price Rs. 1,149 but no rating available.
(24 of 27 matching products are in stock; prices Rs. 249–Rs. 2,144; 11 rated 4+)
```

## `women cotton kurta under 500`

Limits understood: price ≤ Rs. 500 · search text for improved: `women cotton kurta`

**Baseline** (358 results, valid PID: None, fits limits: None)

```
There are no good products that fit the request based on the retrieved results.
```

**Improved** (358 results, status `ok`, valid PID: True, fits limits: True)

```
- Best Product: [7] KTAFZFFP54CXBCHY Women Striped Pure Cotton Straight Kurta  (Green)
- Why: Women Striped Pure Cotton Straight Kurta (Green) is under Rs. 500 (Rs. 495) and made of Pure Cotton, matching the user’s material preference and price limit.
- Alternative: [3] KTAFZFX7HTMGQCG6 Women Solid Cotton Blend Straight Kurta  (Black) - Women Solid Cotton Blend Straight Kurta (Black) is also under Rs. 500 (Rs. 390) but uses Cotton Blend instead of Pure Cotton.
(44 of 358 matching products are in stock and fit price ≤ Rs. 500; prices Rs. 390–Rs. 499; 27 rated 4+)
```

## `men running shoes rating above 4`

Limits understood: rating ≥ 4.0 · search text for improved: `men running shoes`

**Baseline** (0 results, valid PID: None, fits limits: None)

```
(no results, RAG not called)
```

**Improved** (37 results, status `unparsed`, valid PID: None, fits limits: None)

```
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
- Why: Cheapest black jeans for women at Rs. 545 with a 4.1/5 rating.
- Alternative: [2] JEAFF3TGFMW6KMBG Regular Women Black Jeans - Next cheapest option at Rs. 649, slightly higher price but better rating of 4.3/5.
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
- Alternative: [2] SWSFZUEBYU5DM9CH Full Sleeve Printed Men Sweatshirt - Next highest rating 4.6/5 and lowest price Rs. 849.
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
- Best Product: [2] TSHFZQBGBQGXVRHJ Printed Men Polo Neck Grey T-Shirt
- Why: Highest rating 4.7/5 and lowest price Rs.449 within 300–600 range
- Alternative: [1] TSHFZQBG3J5GREG2 Printed Men Polo Neck Black T-Shirt - Same rating 4.7/5 but higher price Rs.499
(680 of 1,440 matching products are in stock and fit price Rs. 300–600; prices Rs. 300–Rs. 600; 250 rated 4+)
```

## `men hooded sweatshirt under 100`

Limits understood: price ≤ Rs. 100 · search text for improved: `men hooded sweatshirt`

**Baseline** (323 results, valid PID: None, fits limits: None)

```
There are no good products that fit the request based on the retrieved results.
```

**Improved** (323 results, status `no_match`, valid PID: None, fits limits: None)

```
None of the 323 products that match your words fits price ≤ Rs. 100. Closest option: Full Sleeve Solid Men Sweatshirt (SWSFYQGK9ZJSMSXN) - the cheapest is Rs. 254. Try relaxing the limit.
```

## `women denim jacket 5 stars under 300`

Limits understood: price ≤ Rs. 300, rating ≥ 5.0 · search text for improved: `women denim jacket`

**Baseline** (0 results, valid PID: None, fits limits: None)

```
(no results, RAG not called)
```

**Improved** (82 results, status `no_match`, valid PID: None, fits limits: None)

```
None of the 82 products that match your words fits price ≤ Rs. 300, rating ≥ 5.0. Closest option: Solid Women Round Neck White T-Shirt (TSHFKYKQ2UHZZAXF) - the cheapest is Rs. 242. Try relaxing the limit.
```

# Data dictionary

All sample files in `data/sample/` are synthetic. They were made up for development and do not describe a real business. The code is in `src/domain_rag_copilot/schemas/`.

## Conventions

- Files are UTF-8 csv with a header row. Column names must match this page exactly. A missing required column or an unknown column is an error, so typos do not pass silently.
- A blank cell means "not given". Required columns must not be blank. Optional blanks become `None` and are never filled with a guess.
- Dates are `YYYY-MM-DD`, no time, no time zone. Weekly sample rows use the Monday of the week. Promotion `start_date` and `end_date` are both included in the promotion.
- Money is a plain number with a dot and no thousands separator (`3.20`). Every money row has a 3 letter uppercase `currency` such as `USD`. Currencies are never converted and the code does not check the code against a list. The sample uses USD.
- `region` and `channel` are free text such as `North` or `store`. Spelling and case must match across files. Blank means not specified, not "all regions".
- Ids are stable text such as `P001`, `PROMO-001`, `CMP-001`, `DOC-001`. They must not contain spaces, `|` or `::`. Do not reuse an id for something else.
- A list of ids in one cell is separated by `|`, for example `P001|P002`.
- Errors are raised as `ValidationError` with the file name and line number (line 1 is the header).

## products_synthetic.csv

One row per product.

| Column | Required | Type | Rule |
|---|---|---|---|
| product_id | yes | id | key, unique |
| product_name | yes | text | |
| category | yes | text | |
| brand | no | text | |

## prices_synthetic.csv

The shelf price a product had on a date, in a region and channel.

| Column | Required | Type | Rule |
|---|---|---|---|
| product_id | yes | id | must exist in products |
| price_date | yes | date | |
| price | yes | number | above 0 |
| currency | yes | text | 3 uppercase letters |
| price_type | yes | text | `regular` or `promotional` |
| region | no | text | |
| channel | no | text | |

Key: product_id + price_date + region + channel, unique.

## promotions_synthetic.csv

One row per promotion. A promotion covers one product. If a real promotion covers three products, use three promotion ids.

| Column | Required | Type | Rule |
|---|---|---|---|
| promotion_id | yes | id | key, unique |
| product_id | yes | id | must exist in products |
| start_date | yes | date | |
| end_date | yes | date | not before start_date |
| discount_type | yes | text | `percent` or `fixed_amount` |
| discount_value | yes | number | above 0. For `percent`, at most 100 (10 means 10 percent) |
| currency | only for fixed_amount | text | 3 uppercase letters |
| region | no | text | |
| channel | no | text | |
| description | no | text | |

Overlapping promotions for the same product are not rejected, because that can happen in real life. Stage 6 will decide how to handle them.

## sales_synthetic.csv

Units and revenue for a product over one date (the sample uses one week per row).

| Column | Required | Type | Rule |
|---|---|---|---|
| product_id | yes | id | must exist in products |
| sale_date | yes | date | |
| units | yes | whole number | 0 or more |
| revenue | yes | number | 0 or more. Revenue above 0 with 0 units is rejected |
| currency | yes | text | 3 uppercase letters |
| cost | no | number | 0 or more |
| region | no | text | |
| channel | no | text | |

Key: product_id + sale_date + region + channel, unique.

Revenue is not checked against units times price, because discounts, returns and rounding can legitimately break that. A sale row with no matching price row is allowed. The sample data happens to have a price for every sale, and a test checks that.

## competitor_prices_synthetic.csv

A price seen for a competitor product on a date.

| Column | Required | Type | Rule |
|---|---|---|---|
| observation_id | yes | id | key, unique |
| competitor_name | yes | text | |
| competitor_product | yes | text | name as the competitor lists it |
| observed_price | yes | number | above 0 |
| currency | yes | text | 3 uppercase letters |
| observation_date | yes | date | |
| source | yes | text | where it was seen, for example a shelf check or a web page |
| product_id | no | id | our matching product. Must exist in products when given |
| region | no | text | |
| channel | no | text | |

`product_id` is optional because some competitor products have no match in our range (CMP-006 in the sample).

## documents_synthetic.csv

Metadata about each source document. The text itself is kept in a separate file under `data/sample/documents/`.

| Column | Required | Type | Rule |
|---|---|---|---|
| document_id | yes | id | key, unique |
| title | yes | text | |
| source_name | yes | text | file or system name shown in citations |
| source_type | yes | text | free text, the sample uses `promotion_brief`, `pricing_report`, `policy` |
| source_path | yes | text | relative to `data/sample/`, forward slashes, no `..` |
| is_synthetic | yes | text | `true` or `false` |
| effective_date | no | date | when the document applies from |
| version | no | text | |
| product_ids | no | id list | each must exist in products |
| promotion_ids | no | id list | each must exist in promotions |
| region | no | text | |
| channel | no | text | |

## How the tables connect

```text
products.product_id  <-  prices.product_id
                     <-  promotions.product_id
                     <-  sales.product_id
                     <-  competitor_prices.product_id   (optional)
                     <-  documents.product_ids           (optional list)
promotions.promotion_id <- documents.promotion_ids       (optional list)
documents.source_path   ->  text file on disk
```

Prices and sales line up on product + date + region + channel. A promotion applies to the price and sales rows of its product whose date is inside the promotion dates and whose region and channel match.

## Why the fields matter later

- Stage 3 (ingestion) reuses these rules for real files and reports failures with file and line.
- Stage 4 (chunking) copies the document metadata onto every chunk. Chunk ids should be `<document_id>::chunk-<number>`, for example `DOC-001::chunk-003`. This is why ids cannot contain `::`.
- Stage 5 (retrieval) can filter by product_ids, promotion_ids, region, channel and effective_date.
- Stage 6 (analytics) needs product_id, dates, units, revenue and price to define a baseline and compare. It also needs region and channel to compare like with like, and currency so amounts are never mixed.
- Stage 8 (answers) builds a citation from document_id, title, source_name, version and effective_date, and warns when `is_synthetic` is true.

## Looking at the sample data

```bash
python -m domain_rag_copilot.schemas
```

This loads every file, checks keys and joins, and prints the row count and first row of each table. In a notebook you can also run `pandas.read_csv("data/sample/sales_synthetic.csv")` to look at a file, but pandas does not apply the rules above.

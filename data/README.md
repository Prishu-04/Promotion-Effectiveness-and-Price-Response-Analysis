# Data notes

Everything in `data/sample/` is synthetic. File names end in `_synthetic`, the document texts start with a synthetic notice, and the document table has an `is_synthetic` column.

Files in `data/sample/`:

- `products_synthetic.csv`, `prices_synthetic.csv`, `promotions_synthetic.csv`, `sales_synthetic.csv`, `competitor_prices_synthetic.csv`
- `documents_synthetic.csv` (metadata) and `documents/*.txt` (text)

Column meanings and rules are in [`docs/data_dictionary.md`](../docs/data_dictionary.md). To check and inspect the files run `python -m domain_rag_copilot.schemas`.

Do not commit real or private business data. Keep it in `data/raw/` or `data/private/`, which git ignores. Generated files such as the Chroma vector store go in `var/`, which git also ignores.

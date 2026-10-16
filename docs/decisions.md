# Decisions

## Made in stage 1

- Dependencies live in `pyproject.toml` only. No `requirements.txt`, so there is one place to edit. Install with `pip install -e ".[dev]"`.
- Python 3.11 or 3.12. Tested on 3.12.3. 3.13 is left out until the later libraries are checked on it.
- Code is in `src/domain_rag_copilot/`. The `src` folder stops Python from importing the package before it is installed.
- Settings come from environment variables or a `.env` file. Real environment variables win. The loader is `load_settings()` in `config.py`.
- Only `python-dotenv` is installed to run the app.
- API keys have `repr=False` in the `Settings` class so they do not show up when settings are printed. Nothing in the code logs them.
- LLM and embedding providers default to `unset`, so nothing needs a key yet.
- Generated files go in `var/` (git ignores it). The default vector store folder is `var/chroma`.
- No `scripts/` folder yet. It gets added when a stage needs a script.

## Made in stage 2

- Schemas are plain dataclasses in `schemas/records.py`, with small checking functions in `schemas/validation.py`. I said in Stage 1 that pydantic would arrive here. I did not add it, because the checks needed (required, type, range, date order, joins) are short in plain Python and easier to read and debug. pydantic can be added later if the API stage needs it.
- Sample data is csv, so it can be opened in Excel or pandas. No database.
- Document text and document metadata are separate files. The metadata row points to the text file with `source_path`.
- Unknown csv columns are errors, so a typo in an optional column name cannot hide.
- Overlapping promotions, sales without prices and revenue that does not equal units times price are not errors. They can happen in real data and Stage 6 decides how to handle them.
- Currency is stored on every money row and never converted.
- Chunk ids will be `<document_id>::chunk-<number>`. Ids cannot contain `::` for that reason.

## Still open

- Which LLM provider and model (needed in Stage 8).
- Which embedding provider and model (needed in Stage 5). A hosted API is easy to install but needs a key and sends text to the provider. `sentence_transformers` runs locally with no key but is a bigger install.
- Base URL and temperature settings are not added yet. They get added in the stage that calls the model.

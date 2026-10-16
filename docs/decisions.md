# Decisions

## Made in stage 1

- Dependencies live in `pyproject.toml` only. No `requirements.txt`, so there is one place to edit. Install with `pip install -e ".[dev]"`.
- Python 3.11 or 3.12. Tested on 3.12.3. 3.13 is left out until the later libraries are checked on it.
- Code is in `src/domain_rag_copilot/`. The `src` folder stops Python from importing the package before it is installed.
- Settings come from environment variables or a `.env` file. Real environment variables win. The loader is `load_settings()` in `config.py`.
- Only `python-dotenv` is installed to run the app. pydantic will be added in Stage 2 when the data schemas need it.
- API keys have `repr=False` in the `Settings` class so they do not show up when settings are printed. Nothing in the code logs them.
- LLM and embedding providers default to `unset`, so nothing needs a key yet.
- Generated files go in `var/` (git ignores it). The default vector store folder is `var/chroma`.
- No `scripts/` folder yet. It gets added when a stage needs a script.

## Still open

- Which LLM provider and model (needed in Stage 8).
- Which embedding provider and model (needed in Stage 5). A hosted API is easy to install but needs a key and sends text to the provider. `sentence_transformers` runs locally with no key but is a bigger install.
- Base URL and temperature settings are not added yet. They get added in the stage that calls the model.

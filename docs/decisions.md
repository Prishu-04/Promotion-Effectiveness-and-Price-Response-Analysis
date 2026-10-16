# Technical decisions

## Made in Stage 1

| # | Decision | Why |
|---|----------|-----|
| D1 | **`pyproject.toml` only** (no `requirements.txt`) | One file holds dependencies, the `src/` package definition, the console script and pytest settings. Later stages add dependencies in one place. Install with `pip install -e ".[dev]"`. |
| D2 | **Python 3.11 and 3.12** (`requires-python = ">=3.11,<3.13"`; `.python-version` = 3.12; Stage 1 verified on 3.12.3) | Later-stage libraries (Chroma, embedding stacks) often lag the newest Python. Widen the range only after verifying. |
| D3 | **`src/` layout**, package `domain_rag_copilot` | Prevents accidentally importing un-installed code; matches README section 8. |
| D4 | **Config = stdlib dataclasses + `python-dotenv`**; no pydantic yet | Only one runtime dependency is justified so far. Pydantic arrives in Stage 2 for data schemas. `load_settings()` / `Settings` is the contract, so its internals can move to `pydantic-settings` later without changing callers. |
| D5 | **Precedence: real environment variables > `.env` > defaults.** `.env` is read from the project root and never copied into `os.environ`. | Predictable; deployments can inject real env vars. |
| D6 | **Secrets are `SecretStr`** (prints `***`) and logging has a redaction filter | README rule: no secrets in files or logs. |
| D7 | **Providers default to `unset`**; API keys blank in `.env.example` | Nothing requires credentials to run Stage 1. |
| D8 | **Runtime artifacts go in `var/`** (default vector store `var/chroma`), git-ignored | Keeps generated files out of version control. |
| D9 | **No `scripts/` folder yet** | No script is needed until ingestion/evaluation (Stage 3+); an empty folder would be a placeholder. |
| D10 | **Logs go to stderr**, program output to stdout | Output stays pipeable. |

Known limitation: `PROJECT_ROOT` is derived from the file location, so the supported workflow is an editable install from a repo checkout. Revisit in Stage 10 (deployment).

## Open decisions (needed before the stage that uses them)

- **LLM provider + model** (needed by Stage 8): set `LLM_PROVIDER`, `LLM_MODEL`, `LLM_API_KEY`.
- **Embedding provider + model** (needed by Stage 5): a hosted API (no heavy install, needs a key, sends text to a provider) vs. local `sentence_transformers` (no key, larger install, works offline). Set `EMBEDDING_PROVIDER`, `EMBEDDING_MODEL`.

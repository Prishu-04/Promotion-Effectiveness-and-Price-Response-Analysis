import os
from dataclasses import dataclass, field
from pathlib import Path
from dotenv import dotenv_values

# this file is src/domain_rag_copilot/config.py, so the project folder is 2 levels up
PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_FILE = PROJECT_ROOT / ".env"
LOG_LEVELS = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
LLM_PROVIDERS = ["unset", "openai", "anthropic", "ollama"]
EMBEDDING_PROVIDERS = ["unset", "openai", "sentence_transformers", "ollama"]


@dataclass
class Settings:
    log_level: str
    llm_provider: str
    llm_model: str
    embedding_provider: str
    embedding_model: str
    data_dir: Path
    sample_data_dir: Path
    vector_store_dir: Path
    # repr=False so the keys never show up if someone prints the settings
    llm_api_key: str = field(default="", repr=False)
    embedding_api_key: str = field(default="", repr=False)

def check_choice(name, value, allowed):
    if value not in allowed:
        raise ValueError(f"{name} is '{value}' but it must be one of: {', '.join(allowed)}")

def load_settings(env_file=ENV_FILE, environ=None):
    values = {}
    if env_file is not None and Path(env_file).is_file():
        values.update(dotenv_values(env_file))
    values.update(os.environ if environ is None else environ)

    def get(name, default=""):
        value = (values.get(name) or "").strip()
        return value or default

    def get_path(name, default):
        path = Path(get(name, default))
        if not path.is_absolute():
            path = PROJECT_ROOT / path
        return path

    log_level = get("LOG_LEVEL", "INFO").upper()
    llm_provider = get("LLM_PROVIDER", "unset").lower()
    embedding_provider = get("EMBEDDING_PROVIDER", "unset").lower()
    check_choice("LOG_LEVEL", log_level, LOG_LEVELS)
    check_choice("LLM_PROVIDER", llm_provider, LLM_PROVIDERS)
    check_choice("EMBEDDING_PROVIDER", embedding_provider, EMBEDDING_PROVIDERS)

    return Settings(
        log_level=log_level,
        llm_provider=llm_provider,
        llm_model=get("LLM_MODEL"),
        embedding_provider=embedding_provider,
        embedding_model=get("EMBEDDING_MODEL"),
        data_dir=get_path("DATA_DIR", "data"),
        sample_data_dir=get_path("SAMPLE_DATA_DIR", "data/sample"),
        vector_store_dir=get_path("VECTOR_STORE_DIR", "var/chroma"),
        llm_api_key=get("LLM_API_KEY"),
        embedding_api_key=get("EMBEDDING_API_KEY"),
    )
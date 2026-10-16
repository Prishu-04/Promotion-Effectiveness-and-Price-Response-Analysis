"""Application configuration.

All settings come from environment variables, optionally loaded from a local
`.env` file at the project root. Real environment variables win over `.env`.

Usage:
    from domain_rag_copilot.config import load_settings
    settings = load_settings()

Secrets (API keys) are wrapped in `SecretStr`, which prints as `***`, so they
cannot leak through `print(settings)`, logging of the settings object, or
tracebacks. Call `.get_secret_value()` only at the moment a provider client
needs the key.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from dotenv import dotenv_values

# src/domain_rag_copilot/config.py -> parents[2] is the project root.
# This assumes the supported workflow: an editable install (`pip install -e .`)
# from a checkout of the repository.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ENV_FILE = PROJECT_ROOT / ".env"

UNSET = "unset"
APP_ENVS = ("local", "test", "production")
LOG_LEVELS = ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")
# Extend these tuples when a later stage adds support for another provider.
LLM_PROVIDERS = (UNSET, "openai", "anthropic", "ollama")
EMBEDDING_PROVIDERS = (UNSET, "openai", "sentence_transformers", "ollama")


class ConfigError(ValueError):
    """Raised when a configuration value is invalid. Messages never contain secrets."""


class SecretStr:
    """Holds a secret and refuses to show it in repr/str."""

    __slots__ = ("_value",)

    def __init__(self, value: str = "") -> None:
        self._value = value

    def get_secret_value(self) -> str:
        return self._value

    def __bool__(self) -> bool:
        return bool(self._value)

    def __repr__(self) -> str:
        return "SecretStr('***')" if self._value else "SecretStr('')"

    __str__ = __repr__


@dataclass(frozen=True)
class LLMSettings:
    provider: str
    model: str
    api_key: SecretStr
    base_url: str
    temperature: float


@dataclass(frozen=True)
class EmbeddingSettings:
    provider: str
    model: str
    api_key: SecretStr
    base_url: str


@dataclass(frozen=True)
class Settings:
    app_env: str
    log_level: str
    project_root: Path
    env_file: Path | None  # the .env file that was actually read, if any
    data_dir: Path
    sample_data_dir: Path
    vector_store_dir: Path
    llm: LLMSettings
    embedding: EmbeddingSettings

    def secret_values(self) -> list[str]:
        """Raw secret strings, used only to redact them from log output."""
        return [s for s in (self.llm.api_key.get_secret_value(),
                            self.embedding.api_key.get_secret_value()) if s]

    def safe_summary(self) -> dict[str, object]:
        """A display-safe view of the settings (keys reported only as set / not set)."""
        return {
            "app_env": self.app_env,
            "log_level": self.log_level,
            "llm": {"provider": self.llm.provider, "model": self.llm.model,
                    "base_url": self.llm.base_url, "temperature": self.llm.temperature,
                    "api_key_set": bool(self.llm.api_key)},
            "embedding": {"provider": self.embedding.provider, "model": self.embedding.model,
                          "base_url": self.embedding.base_url,
                          "api_key_set": bool(self.embedding.api_key)},
        }


def _read(env: Mapping[str, str], key: str, default: str = "") -> str:
    """Value for `key`, or `default` if it is missing or blank."""
    value = env.get(key)
    if value is None or not value.strip():
        return default
    return value.strip()


def _choice(
    env: Mapping[str, str],
    key: str,
    allowed: tuple[str, ...],
    default: str,
    *,
    upper: bool = False,
) -> str:
    value = _read(env, key, default)
    value = value.upper() if upper else value.lower()
    if value not in allowed:
        raise ConfigError(f"{key}={value!r} is not valid. Allowed values: {', '.join(allowed)}.")
    return value


def _temperature(env: Mapping[str, str]) -> float:
    raw = _read(env, "LLM_TEMPERATURE", "0.0")
    try:
        value = float(raw)
    except ValueError:
        raise ConfigError(f"LLM_TEMPERATURE={raw!r} is not a number (expected e.g. 0.0).") from None
    if not 0.0 <= value <= 2.0:
        raise ConfigError(f"LLM_TEMPERATURE={raw!r} must be between 0.0 and 2.0.")
    return value


def _path(env: Mapping[str, str], key: str, default: str, root: Path) -> Path:
    path = Path(_read(env, key, default)).expanduser()
    return path if path.is_absolute() else root / path


def settings_from_mapping(
    env: Mapping[str, str],
    *,
    project_root: Path = PROJECT_ROOT,
    env_file: Path | None = None,
) -> Settings:
    """Build validated Settings from a plain mapping (no file or OS access)."""
    return Settings(
        app_env=_choice(env, "APP_ENV", APP_ENVS, "local"),
        log_level=_choice(env, "LOG_LEVEL", LOG_LEVELS, "INFO", upper=True),
        project_root=project_root,
        env_file=env_file,
        data_dir=_path(env, "DATA_DIR", "data", project_root),
        sample_data_dir=_path(env, "SAMPLE_DATA_DIR", "data/sample", project_root),
        vector_store_dir=_path(env, "VECTOR_STORE_DIR", "var/chroma", project_root),
        llm=LLMSettings(
            provider=_choice(env, "LLM_PROVIDER", LLM_PROVIDERS, UNSET),
            model=_read(env, "LLM_MODEL"),
            api_key=SecretStr(_read(env, "LLM_API_KEY")),
            base_url=_read(env, "LLM_BASE_URL"),
            temperature=_temperature(env),
        ),
        embedding=EmbeddingSettings(
            provider=_choice(env, "EMBEDDING_PROVIDER", EMBEDDING_PROVIDERS, UNSET),
            model=_read(env, "EMBEDDING_MODEL"),
            api_key=SecretStr(_read(env, "EMBEDDING_API_KEY")),
            base_url=_read(env, "EMBEDDING_BASE_URL"),
        ),
    )


def load_settings(
    env_file: Path | None = DEFAULT_ENV_FILE,
    environ: Mapping[str, str] | None = None,
) -> Settings:
    """Load settings from `env_file` (if it exists) overlaid by environment variables.

    Pass `env_file=None, environ={...}` in tests for a fully isolated config.
    """
    file_values: dict[str, str] = {}
    used_file: Path | None = None
    if env_file is not None and env_file.is_file():
        file_values = {k: v for k, v in dotenv_values(env_file).items() if v is not None}
        used_file = env_file
    merged = {**file_values, **(os.environ if environ is None else environ)}
    return settings_from_mapping(merged, env_file=used_file)

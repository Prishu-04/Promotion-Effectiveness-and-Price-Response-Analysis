import pytest

from domain_rag_copilot.config import ConfigError, load_settings


def test_defaults_need_no_credentials():
    s = load_settings(env_file=None, environ={})
    assert (s.app_env, s.log_level) == ("local", "INFO")
    assert s.llm.provider == "unset" and not s.llm.api_key
    assert s.embedding.provider == "unset"
    assert s.vector_store_dir == s.project_root / "var" / "chroma"


def test_invalid_provider_gives_helpful_error():
    with pytest.raises(ConfigError, match="LLM_PROVIDER"):
        load_settings(env_file=None, environ={"LLM_PROVIDER": "not-a-provider"})


def test_api_key_never_appears_in_repr_or_summary():
    key = "sk-test-1234567890"
    s = load_settings(env_file=None, environ={"LLM_API_KEY": key, "EMBEDDING_API_KEY": key})
    assert key not in repr(s) and key not in str(s.safe_summary())
    assert s.llm.api_key.get_secret_value() == key

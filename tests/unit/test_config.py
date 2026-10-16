import pytest
from domain_rag_copilot.config import load_settings

def test_defaults():
    settings = load_settings(env_file=None, environ={})
    assert settings.log_level == "INFO"
    assert settings.llm_provider == "unset"
    assert settings.embedding_provider == "unset"
    assert settings.vector_store_dir.name == "chroma"

def test_bad_provider_gives_clear_error():
    with pytest.raises(ValueError, match="LLM_PROVIDER"):
        load_settings(env_file=None, environ={"LLM_PROVIDER": "banana"})

def test_api_key_is_not_in_repr():
    settings = load_settings(env_file=None, environ={"LLM_API_KEY": "sk-test-12345"})
    assert settings.llm_api_key == "sk-test-12345"
    assert "sk-test-12345" not in repr(settings)
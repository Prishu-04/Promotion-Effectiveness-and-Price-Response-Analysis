from domain_rag_copilot.cli import main
from domain_rag_copilot.config import load_settings


def test_app_starts_without_any_keys():
    # empty environ and no .env file, so nothing from the real machine leaks in
    settings = load_settings(env_file=None, environ={})
    assert main(settings=settings) == 0

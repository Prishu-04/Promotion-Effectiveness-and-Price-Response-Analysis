"""Stage 1 smoke test: the package imports, config loads and the health check runs
with no .env file and no credentials."""

from domain_rag_copilot import __version__
from domain_rag_copilot.cli import main
from domain_rag_copilot.config import load_settings
from domain_rag_copilot.health import run_health_check


def test_package_starts_without_credentials():
    settings = load_settings(env_file=None, environ={})  # isolated: ignores real .env / OS env

    report = run_health_check(settings)

    assert __version__
    assert report.ok
    assert main(["health"], settings=settings) == 0

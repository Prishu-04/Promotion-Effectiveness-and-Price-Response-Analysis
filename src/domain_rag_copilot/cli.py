"""Command-line entry point: `python -m domain_rag_copilot` or `domain-rag-copilot`."""

from __future__ import annotations

import argparse
import logging
import sys
from typing import Sequence

from domain_rag_copilot import __version__
from domain_rag_copilot.config import ConfigError, Settings, load_settings
from domain_rag_copilot.health import format_report, run_health_check
from domain_rag_copilot.logging_setup import configure_logging

logger = logging.getLogger(__name__)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="domain-rag-copilot",
        description="Domain RAG Copilot (P7-034). Stage 1 provides only the health check.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    commands = parser.add_subparsers(dest="command")
    commands.add_parser("health", help="verify the package imports and configuration loads (default)")
    return parser


def main(argv: Sequence[str] | None = None, *, settings: Settings | None = None) -> int:
    """Run the CLI. Returns an exit code: 0 ok, 1 health failed, 2 configuration error.

    `settings` can be injected (used by tests); normally it is loaded from .env/environment.
    """
    build_parser().parse_args(argv)  # only `health` exists, so it is also the default

    if settings is None:
        try:
            settings = load_settings()
        except ConfigError as exc:
            print(f"Configuration error: {exc}", file=sys.stderr)
            print("Fix the value in your .env file (see .env.example).", file=sys.stderr)
            return 2

    configure_logging(settings.log_level, secrets=settings.secret_values())
    logger.info("Starting health check (app_env=%s)", settings.app_env)
    report = run_health_check(settings)
    print(format_report(report))
    return 0 if report.ok else 1

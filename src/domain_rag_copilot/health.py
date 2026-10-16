"""Health / smoke check: confirms the package imports and the configuration loads.

This is the Stage 1 "does it start?" check. It makes no network calls and needs
no credentials.
"""

from __future__ import annotations

import logging
import sys
from dataclasses import dataclass

from domain_rag_copilot import __version__
from domain_rag_copilot.config import UNSET, Settings

logger = logging.getLogger(__name__)

MIN_PYTHON = (3, 11)
MAX_PYTHON_EXCLUSIVE = (3, 13)
PROVIDERS_NEEDING_API_KEY = ("openai", "anthropic")

# Status values: "ok", "info" (nothing to do), "warn" (fix before the stage that needs it), "fail".


@dataclass(frozen=True)
class Check:
    name: str
    status: str
    detail: str


@dataclass(frozen=True)
class HealthReport:
    version: str
    checks: tuple[Check, ...]

    @property
    def ok(self) -> bool:
        return all(check.status != "fail" for check in self.checks)


def _python_check() -> Check:
    current = sys.version_info[:2]
    text = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    if current < MIN_PYTHON:
        return Check("python", "fail", f"{text} is too old; need 3.11 or 3.12")
    if current >= MAX_PYTHON_EXCLUSIVE:
        return Check("python", "warn", f"{text} is newer than the tested range (3.11-3.12)")
    return Check("python", "ok", f"{text} (supported: 3.11-3.12)")


def _provider_check(name: str, provider: str, model: str, has_key: bool) -> Check:
    if provider == UNSET:
        return Check(name, "info", "not configured yet (not needed for Stage 1)")
    problems = []
    if not model:
        problems.append("model name is blank")
    if provider in PROVIDERS_NEEDING_API_KEY and not has_key:
        problems.append("API key is not set")
    if problems:
        return Check(name, "warn", f"provider={provider}; " + "; ".join(problems))
    return Check(name, "ok", f"provider={provider}, model={model}, api_key={'set' if has_key else 'not needed'}")


def run_health_check(settings: Settings) -> HealthReport:
    source = str(settings.env_file) if settings.env_file else "environment/defaults (no .env found)"
    checks = (
        _python_check(),
        Check("package", "ok", f"domain_rag_copilot {__version__} imported"),
        Check("config", "ok", f"app_env={settings.app_env}, log_level={settings.log_level}, source={source}"),
        _provider_check("llm", settings.llm.provider, settings.llm.model, bool(settings.llm.api_key)),
        _provider_check("embedding", settings.embedding.provider, settings.embedding.model,
                        bool(settings.embedding.api_key)),
    )
    report = HealthReport(version=__version__, checks=checks)
    logger.info("Health check finished: ok=%s", report.ok)
    return report


def format_report(report: HealthReport) -> str:
    lines = [f"Domain RAG Copilot {report.version} - health check"]
    lines += [f"  [{c.status.upper():<4}] {c.name:<9} {c.detail}" for c in report.checks]
    lines.append("Result: OK" if report.ok else "Result: FAILED")
    return "\n".join(lines)

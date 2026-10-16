"""Logging setup with a safety net that redacts known secret values."""

from __future__ import annotations

import logging
import sys
from typing import Iterable

LOG_FORMAT = "%(asctime)s %(levelname)-8s %(name)s: %(message)s"
_HANDLER_MARK = "_domain_rag_copilot_handler"


class RedactingFilter(logging.Filter):
    """Replaces any occurrence of a known secret in a log message with `***`."""

    def __init__(self, secrets: Iterable[str]) -> None:
        super().__init__()
        self._secrets = [s for s in secrets if s]

    def filter(self, record: logging.LogRecord) -> bool:
        if self._secrets:
            message = record.getMessage()
            for secret in self._secrets:
                message = message.replace(secret, "***")
            record.msg, record.args = message, None
        return True


def configure_logging(level: str = "INFO", secrets: Iterable[str] = ()) -> None:
    """Send logs to stderr (stdout stays clean for program output). Safe to call repeatedly."""
    root = logging.getLogger()
    for handler in list(root.handlers):
        if getattr(handler, _HANDLER_MARK, False):
            root.removeHandler(handler)

    handler = logging.StreamHandler(sys.stderr)
    setattr(handler, _HANDLER_MARK, True)
    handler.setFormatter(logging.Formatter(LOG_FORMAT))
    handler.addFilter(RedactingFilter(secrets))
    root.addHandler(handler)
    root.setLevel(level)

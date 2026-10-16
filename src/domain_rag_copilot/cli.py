import logging
import sys
from domain_rag_copilot.config import load_settings
from domain_rag_copilot.health import run_health_check
from domain_rag_copilot.logging_setup import setup_logging
logger = logging.getLogger(__name__)
def main(settings=None):
    """Run the health check. Returns 0 if ok, 1 if a problem was found, 2 for a bad config."""
    if settings is None:
        try:
            settings = load_settings()
        except ValueError as error:
            print(f"config problem: {error}", file=sys.stderr)
            return 2
    setup_logging(settings.log_level)
    logger.info("running health check")
    if run_health_check(settings):
        return 0
    return 1

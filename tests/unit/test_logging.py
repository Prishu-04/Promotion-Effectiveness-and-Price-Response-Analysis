import logging

from domain_rag_copilot.logging_setup import RedactingFilter


def test_redacting_filter_hides_secret_in_log_message():
    record = logging.LogRecord("t", logging.INFO, __file__, 1, "key is %s", ("sk-test-1234567890",), None)
    RedactingFilter(["sk-test-1234567890"]).filter(record)
    assert "sk-test-1234567890" not in record.getMessage()
    assert "***" in record.getMessage()

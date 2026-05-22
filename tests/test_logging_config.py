from __future__ import annotations

import json
import logging

from innovanote_observability.log_events import LogEvent
from innovanote_observability.logging_context import LogContext


class TestJsonFormatter:
    def test_emits_valid_json_with_canonical_fields(self, capture_json_logs):
        logger = logging.getLogger("test_emits_valid_json")
        logger.info("hello world")
        line = capture_json_logs.getvalue().strip().splitlines()[-1]
        payload = json.loads(line)
        assert payload["message"] == "hello world"
        assert payload["level"] == "INFO"
        assert payload["service"] == "test-service"
        assert payload["environment"] == "test"
        assert payload["version"] == "0.0.1"
        assert "timestamp" in payload

    def test_includes_contextvars_when_present(self, capture_json_logs):
        logger = logging.getLogger("test_includes_contextvars")
        with LogContext(correlation_id="cid-1", user_id="u-9", recording_id="rec-7"):
            logger.info("with context")
        line = capture_json_logs.getvalue().strip().splitlines()[-1]
        payload = json.loads(line)
        assert payload["correlation_id"] == "cid-1"
        assert payload["user_id"] == "u-9"
        assert payload["recording_id"] == "rec-7"

    def test_extra_event_is_carried_through(self, capture_json_logs):
        logger = logging.getLogger("test_event")
        logger.info("ev", extra={"event": LogEvent.RECORDING_UPLOADED, "recording_id": "r"})
        payload = json.loads(capture_json_logs.getvalue().strip().splitlines()[-1])
        assert payload["event"] in (LogEvent.RECORDING_UPLOADED, "recording_uploaded")
        assert payload["recording_id"] == "r"

    def test_redacts_sensitive_in_extra(self, capture_json_logs):
        logger = logging.getLogger("test_redact_extra")
        logger.info("login", extra={"password": "supersecret"})
        payload = json.loads(capture_json_logs.getvalue().strip().splitlines()[-1])
        assert payload["password"] == "[REDACTED]"

    def test_exception_info_serialized(self, capture_json_logs):
        logger = logging.getLogger("test_exc")
        try:
            raise ValueError("boom")
        except ValueError:
            logger.exception("oops")
        payload = json.loads(capture_json_logs.getvalue().strip().splitlines()[-1])
        assert "exception" in payload
        assert "ValueError" in payload["exception"]

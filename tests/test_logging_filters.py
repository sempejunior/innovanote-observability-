from __future__ import annotations

import logging

from innovanote_observability.logging_context import LogContext
from innovanote_observability.logging_filters import (
    RequestContextFilter,
    SensitiveDataFilter,
    redact_value,
)


class TestRedactValue:
    def test_redacts_known_sensitive_keys(self):
        result = redact_value("supersecret", key="password")
        assert result == "[REDACTED]"

    def test_redacts_authorization_key(self):
        result = redact_value({"Authorization": "Bearer abc.def.ghi"})
        assert result == {"Authorization": "[REDACTED]"}

    def test_redacts_bearer_token_inline(self):
        result = redact_value("Authorization: Bearer abc.def.ghi")
        assert "[REDACTED]" in result

    def test_redacts_jwt_string(self):
        jwt = "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjMifQ.abc-DEF_123"
        result = redact_value(f"received {jwt} from header")
        assert "[JWT_REDACTED]" in result
        assert "from header" in result

    def test_redacts_database_url_password(self):
        result = redact_value("postgres://user:secret@host:5432/db")
        assert "secret" not in result
        assert "[REDACTED]" in result

    def test_passes_through_non_sensitive_data(self):
        assert redact_value(42) == 42
        assert redact_value("hello") == "hello"
        assert redact_value([1, 2, 3]) == [1, 2, 3]

    def test_recurses_into_nested_dicts_and_lists(self):
        payload = {"user": {"email": "x@y.com", "token": "xxx"}, "items": ["a", {"password": "p"}]}
        result = redact_value(payload)
        assert result["user"]["token"] == "[REDACTED]"
        assert result["items"][1]["password"] == "[REDACTED]"


class TestSensitiveDataFilter:
    def test_redacts_msg_string(self):
        record = logging.LogRecord(
            name="t", level=logging.INFO, pathname="x.py", lineno=1,
            msg="Bearer abc.def.ghi was leaked", args=(), exc_info=None,
        )
        SensitiveDataFilter().filter(record)
        assert "[REDACTED]" in record.msg

    def test_redacts_tuple_args(self):
        record = logging.LogRecord(
            name="t", level=logging.INFO, pathname="x.py", lineno=1,
            msg="login token=%s", args=("Bearer abc.def.ghi",), exc_info=None,
        )
        SensitiveDataFilter().filter(record)
        assert "[REDACTED]" in record.args[0]


class TestRequestContextFilter:
    def test_injects_service_environment_version(self):
        record = logging.LogRecord(
            name="t", level=logging.INFO, pathname="x.py", lineno=1,
            msg="hi", args=(), exc_info=None,
        )
        RequestContextFilter(
            service_name="svc", environment="prod", service_version="1.2.3"
        ).filter(record)
        assert record.service == "svc"
        assert record.environment == "prod"
        assert record.version == "1.2.3"

    def test_pulls_context_vars(self):
        record = logging.LogRecord(
            name="t", level=logging.INFO, pathname="x.py", lineno=1,
            msg="hi", args=(), exc_info=None,
        )
        with LogContext(correlation_id="cid-42", user_id="u-1"):
            RequestContextFilter().filter(record)
        assert record.correlation_id == "cid-42"
        assert record.user_id == "u-1"

    def test_preserves_existing_record_attrs(self):
        record = logging.LogRecord(
            name="t", level=logging.INFO, pathname="x.py", lineno=1,
            msg="hi", args=(), exc_info=None,
        )
        record.correlation_id = "explicit"
        RequestContextFilter().filter(record)
        assert record.correlation_id == "explicit"

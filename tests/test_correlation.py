from __future__ import annotations

from innovanote_observability.correlation import (
    CORRELATION_HEADER,
    SQS_CORRELATION_ATTR,
    SQS_TRACE_ATTR,
    build_sqs_message_attributes,
    ensure_correlation_id,
    extract_from_http_headers,
    extract_from_sqs_message,
    extract_trace_from_http_headers,
    generate_correlation_id,
    inject_into_http_response_headers,
)
from innovanote_observability.logging_context import LogContext, correlation_id_context


class TestGenerate:
    def test_generates_unique_ids(self):
        a = generate_correlation_id()
        b = generate_correlation_id()
        assert a != b
        assert isinstance(a, str)
        assert len(a) >= 10


class TestExtractHttp:
    def test_returns_correlation_id_case_insensitive(self):
        cid = extract_from_http_headers({"x-correlation-id": "abc"})
        assert cid == "abc"

    def test_returns_request_id_fallback(self):
        cid = extract_from_http_headers({"X-Request-ID": "req-1"})
        assert cid == "req-1"

    def test_returns_none_when_absent(self):
        assert extract_from_http_headers({}) is None
        assert extract_from_http_headers({"other": "h"}) is None

    def test_extracts_amzn_trace(self):
        trace = extract_trace_from_http_headers({"X-Amzn-Trace-Id": "Root=1-abc"})
        assert trace == "Root=1-abc"


class TestInjectHttp:
    def test_sets_header(self):
        headers: dict[str, str] = {}
        inject_into_http_response_headers(headers, "cid-1")
        assert headers[CORRELATION_HEADER] == "cid-1"


class TestBuildSqsAttributes:
    def test_uses_explicit_correlation_id(self):
        attrs = build_sqs_message_attributes(correlation_id="c1", trace_id="t1")
        assert attrs[SQS_CORRELATION_ATTR]["StringValue"] == "c1"
        assert attrs[SQS_TRACE_ATTR]["StringValue"] == "t1"
        assert attrs[SQS_CORRELATION_ATTR]["DataType"] == "String"

    def test_falls_back_to_context(self):
        with LogContext(correlation_id="from-ctx"):
            attrs = build_sqs_message_attributes()
        assert attrs[SQS_CORRELATION_ATTR]["StringValue"] == "from-ctx"

    def test_returns_empty_when_no_context(self):
        attrs = build_sqs_message_attributes()
        assert attrs == {}

    def test_includes_extra(self):
        attrs = build_sqs_message_attributes(correlation_id="c", extra={"user_id": "u"})
        assert attrs["user_id"]["StringValue"] == "u"

    def test_skips_none_extra(self):
        attrs = build_sqs_message_attributes(correlation_id="c", extra={"user_id": None})
        assert "user_id" not in attrs


class TestExtractFromSqs:
    def test_extracts_from_boto3_payload(self):
        message = {
            "MessageAttributes": {
                "correlation_id": {"DataType": "String", "StringValue": "cid"},
                "trace_id": {"DataType": "String", "StringValue": "tid"},
            }
        }
        result = extract_from_sqs_message(message)
        assert result == {"correlation_id": "cid", "trace_id": "tid"}

    def test_extracts_from_lambda_event_record(self):
        message = {
            "messageAttributes": {
                "correlation_id": {"stringValue": "cid", "dataType": "String"},
            }
        }
        result = extract_from_sqs_message(message)
        assert result["correlation_id"] == "cid"
        assert result["trace_id"] is None

    def test_returns_nones_when_no_attributes(self):
        assert extract_from_sqs_message({}) == {"correlation_id": None, "trace_id": None}


class TestEnsureCorrelationId:
    def test_returns_existing(self):
        correlation_id_context.set("existing")
        assert ensure_correlation_id() == "existing"

    def test_generates_and_sets_when_absent(self):
        new = ensure_correlation_id()
        assert correlation_id_context.get() == new

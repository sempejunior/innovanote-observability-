from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from innovanote_observability.exceptions import SQSException
from innovanote_observability.logging_context import LogContext, correlation_id_context
from innovanote_observability.sqs_helpers import publish, sqs_message_context


class TestPublish:
    def test_publish_injects_correlation_from_context(self):
        client = MagicMock()
        client.send_message.return_value = {"MessageId": "msg-1"}
        with LogContext(correlation_id="cid-1"):
            publish("https://sqs/q", {"foo": "bar"}, client=client)
        kwargs = client.send_message.call_args.kwargs
        assert kwargs["QueueUrl"] == "https://sqs/q"
        attrs = kwargs["MessageAttributes"]
        assert attrs["correlation_id"]["StringValue"] == "cid-1"

    def test_publish_explicit_overrides_context(self):
        client = MagicMock()
        client.send_message.return_value = {"MessageId": "x"}
        with LogContext(correlation_id="from-ctx"):
            publish("u", "payload", correlation_id="explicit", client=client)
        attrs = client.send_message.call_args.kwargs["MessageAttributes"]
        assert attrs["correlation_id"]["StringValue"] == "explicit"

    def test_publish_serializes_dict_payload(self):
        client = MagicMock()
        client.send_message.return_value = {"MessageId": "x"}
        publish("u", {"k": "v"}, client=client)
        body = client.send_message.call_args.kwargs["MessageBody"]
        assert "k" in body and "v" in body

    def test_publish_passes_through_string_payload(self):
        client = MagicMock()
        client.send_message.return_value = {"MessageId": "x"}
        publish("u", "raw-string", client=client)
        assert client.send_message.call_args.kwargs["MessageBody"] == "raw-string"

    def test_publish_raises_sqs_exception_on_failure(self):
        client = MagicMock()
        client.send_message.side_effect = RuntimeError("connection error")
        with pytest.raises(SQSException) as info:
            publish("u", {"a": 1}, client=client)
        assert info.value.details == {"queue_url": "u"}

    def test_publish_fifo_kwargs(self):
        client = MagicMock()
        client.send_message.return_value = {"MessageId": "x"}
        publish(
            "u",
            {"a": 1},
            client=client,
            message_group_id="g",
            message_deduplication_id="d",
        )
        kwargs = client.send_message.call_args.kwargs
        assert kwargs["MessageGroupId"] == "g"
        assert kwargs["MessageDeduplicationId"] == "d"


class TestSqsMessageContext:
    def test_opens_log_context_from_message(self):
        message = {
            "MessageId": "m-1",
            "MessageAttributes": {
                "correlation_id": {"DataType": "String", "StringValue": "cid-from-msg"},
                "trace_id": {"DataType": "String", "StringValue": "tid-from-msg"},
            },
        }
        with sqs_message_context(message):
            assert correlation_id_context.get() == "cid-from-msg"

    def test_handles_missing_attributes_gracefully(self):
        message = {"MessageId": "m-2"}
        with sqs_message_context(message):
            assert correlation_id_context.get() is None

from __future__ import annotations

import asyncio
import json

import pytest

from innovanote_observability.instrumentation import (
    observed,
    sqs_message_handler,
)
from innovanote_observability.logging_context import correlation_id_context


def _last(buffer) -> dict:
    return json.loads(buffer.getvalue().strip().splitlines()[-1])


def _last_op(buffer, event: str) -> dict:
    for line in reversed(buffer.getvalue().strip().splitlines()):
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if payload.get("event") == event:
            return payload
    raise AssertionError(f"no log line with event={event!r} in buffer")


class TestObserved:
    def test_bare_decorator_works_sync(self, capture_json_logs):
        @observed
        def add(a: int, b: int) -> int:
            return a + b

        assert add(1, 2) == 3
        completed = _last_op(capture_json_logs, "operation_completed")
        assert "duration_ms" in completed

    def test_decorator_with_args(self, capture_json_logs):
        @observed(operation="add_op", include_args=True)
        def add(a: int, b: int) -> int:
            return a + b

        add(1, 2)
        started = _last_op(capture_json_logs, "operation_started")
        assert started["operation"] == "add_op"
        assert started["call_args"] == [1, 2]

    def test_async(self, capture_json_logs):
        @observed
        async def f() -> str:
            await asyncio.sleep(0)
            return "ok"

        assert asyncio.run(f()) == "ok"
        _last_op(capture_json_logs, "operation_completed")

    def test_logs_exception(self, capture_json_logs):
        @observed
        def boom():
            raise ValueError("nope")

        with pytest.raises(ValueError):
            boom()
        failed = _last_op(capture_json_logs, "operation_failed")
        assert failed["exception_type"] == "ValueError"


class TestSqsMessageHandler:
    def test_opens_correlation_from_message(self, capture_json_logs):
        captured: dict[str, str | None] = {}

        @sqs_message_handler
        def process(message: dict) -> None:
            captured["cid"] = correlation_id_context.get()

        message = {
            "MessageId": "m-1",
            "MessageAttributes": {
                "correlation_id": {"DataType": "String", "StringValue": "cid-from-msg"},
            },
        }
        process(message)
        assert captured["cid"] == "cid-from-msg"
        assert correlation_id_context.get() is None

    def test_logs_message_consumed_then_op_complete(self, capture_json_logs):
        @sqs_message_handler
        def process(message: dict) -> None:
            return None

        process({"MessageId": "m-1", "MessageAttributes": {}})
        lines = capture_json_logs.getvalue().strip().splitlines()
        events = [json.loads(line).get("event") for line in lines]
        assert "sqs_message_consumed" in events
        assert "operation_completed" in events

    def test_propagates_exception(self):
        @sqs_message_handler
        def process(message: dict) -> None:
            raise RuntimeError("kaboom")

        with pytest.raises(RuntimeError):
            process({"MessageId": "m-1", "MessageAttributes": {}})

    def test_async_handler(self):
        @sqs_message_handler
        async def process(message: dict) -> str:
            return correlation_id_context.get() or "none"

        result = asyncio.run(
            process(
                {
                    "MessageId": "m-1",
                    "MessageAttributes": {
                        "correlation_id": {"DataType": "String", "StringValue": "cid-async"},
                    },
                }
            )
        )
        assert result == "cid-async"

    def test_raises_when_message_missing(self):
        @sqs_message_handler
        def process(message: dict) -> None:
            ...

        with pytest.raises(ValueError):
            process()  # type: ignore[call-arg]

    def test_message_arg_position(self):
        @sqs_message_handler(message_arg=1)
        def process(ctx: dict, message: dict) -> str | None:
            return correlation_id_context.get()

        result = process(
            {"some": "ctx"},
            {
                "MessageId": "m",
                "MessageAttributes": {
                    "correlation_id": {"DataType": "String", "StringValue": "cid-pos1"},
                },
            },
        )
        assert result == "cid-pos1"


class TestInstrument:
    def test_instrument_registers_middleware_handlers_and_health(self, monkeypatch):
        pytest.importorskip("fastapi")
        from fastapi import FastAPI
        from fastapi.testclient import TestClient

        from innovanote_observability.middleware_fastapi import instrument

        app = FastAPI()
        instrument(app, service_name="instrumented-service")

        client = TestClient(app)
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json() == {"status": "ok"}
        assert r.headers.get("X-Correlation-ID")

        r2 = client.get("/ready")
        assert r2.status_code == 200
        assert r2.json() == {"status": "ready"}

    def test_instrument_handles_app_exception(self):
        pytest.importorskip("fastapi")
        from fastapi import FastAPI
        from fastapi.testclient import TestClient

        from innovanote_observability import (
            ErrorCode,
            NotFoundException,
        )
        from innovanote_observability.middleware_fastapi import instrument

        app = FastAPI()
        instrument(app)

        @app.get("/missing")
        def missing():
            raise NotFoundException(error_code=ErrorCode.NOTE_NOT_FOUND)

        client = TestClient(app)
        r = client.get("/missing")
        assert r.status_code == 404
        assert r.json()["error"]["code"] == "NOTE_NOT_FOUND"

    def test_instrument_can_disable_health_routes(self):
        pytest.importorskip("fastapi")
        from fastapi import FastAPI
        from fastapi.testclient import TestClient

        from innovanote_observability.middleware_fastapi import instrument

        app = FastAPI()
        instrument(app, add_health_routes=False)

        client = TestClient(app)
        assert client.get("/health").status_code == 404


class TestAutoConfig:
    def test_get_logger_triggers_auto_config(self, monkeypatch):
        from innovanote_observability import logging_config

        monkeypatch.setattr(logging_config, "_configured", False)
        assert logging_config.is_configured() is False
        logging_config.get_logger("x")
        assert logging_config.is_configured() is True


class TestSqsSubmodule:
    def test_submodule_exposes_publish(self):
        from innovanote_observability import sqs

        assert callable(sqs.publish)
        assert callable(sqs.sqs_message_context)

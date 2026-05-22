from __future__ import annotations

import asyncio
import json

import pytest

from innovanote_observability.exceptions import NotFoundException
from innovanote_observability.logging_context import correlation_id_context
from innovanote_observability.logging_decorators import (
    log_errors,
    log_operation,
    log_performance,
    with_context,
)


def _last_record(buffer) -> dict:
    return json.loads(buffer.getvalue().strip().splitlines()[-1])


class TestLogOperation:
    def test_sync_success_logs_start_and_end(self, capture_json_logs):
        @log_operation("do_work")
        def f(x: int) -> int:
            return x + 1

        assert f(1) == 2
        lines = capture_json_logs.getvalue().strip().splitlines()
        assert len(lines) >= 2
        assert json.loads(lines[-2])["event"] == "operation_started"
        end = json.loads(lines[-1])
        assert end["event"] == "operation_completed"
        assert end["duration_ms"] >= 0

    def test_sync_failure_logs_error_with_error_code(self, capture_json_logs):
        @log_operation("fail_op")
        def f():
            raise NotFoundException()

        with pytest.raises(NotFoundException):
            f()
        last = _last_record(capture_json_logs)
        assert last["event"] == "operation_failed"
        assert last["error_code"] == "NOT_FOUND"
        assert last["exception_type"] == "NotFoundException"

    def test_async_success(self, capture_json_logs):
        @log_operation("async_op")
        async def f() -> str:
            await asyncio.sleep(0)
            return "ok"

        result = asyncio.run(f())
        assert result == "ok"
        last = _last_record(capture_json_logs)
        assert last["event"] == "operation_completed"

    def test_async_failure(self, capture_json_logs):
        @log_operation("async_fail")
        async def f():
            raise RuntimeError("nope")

        with pytest.raises(RuntimeError):
            asyncio.run(f())
        last = _last_record(capture_json_logs)
        assert last["event"] == "operation_failed"
        assert last["exception_type"] == "RuntimeError"

    def test_include_args_recorded_in_start(self, capture_json_logs):
        @log_operation("with_args", include_args=True)
        def f(a, b=2):
            return a + b

        f(1, b=3)
        start = json.loads(capture_json_logs.getvalue().strip().splitlines()[0])
        assert start["call_args"] == [1]
        assert start["call_kwargs"] == {"b": 3}


class TestLogPerformance:
    def test_emits_at_debug(self, capture_json_logs):
        @log_performance("perf")
        def f():
            return 1

        f()
        lines = capture_json_logs.getvalue().strip().splitlines()
        assert any(json.loads(line)["level"] == "DEBUG" for line in lines)


class TestLogErrors:
    def test_logs_only_on_failure(self, capture_json_logs):
        @log_errors("err_op")
        def f(ok: bool):
            if not ok:
                raise ValueError("bad")
            return 1

        f(True)
        first_output = capture_json_logs.getvalue()
        assert first_output == ""

        with pytest.raises(ValueError):
            f(False)
        last = _last_record(capture_json_logs)
        assert last["event"] == "operation_failed"


class TestWithContext:
    def test_sync_sets_and_clears(self):
        @with_context(correlation_id="cid-x")
        def f():
            return correlation_id_context.get()

        assert f() == "cid-x"
        assert correlation_id_context.get() is None

    def test_async(self):
        @with_context(correlation_id="cid-a")
        async def f():
            return correlation_id_context.get()

        assert asyncio.run(f()) == "cid-a"

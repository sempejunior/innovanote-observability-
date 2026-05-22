from __future__ import annotations

from innovanote_observability.logging_context import (
    LogContext,
    clear_context,
    correlation_id_context,
    get_correlation_id,
    get_trace_id,
    log_context,
    set_context,
    snapshot_context,
    user_id_context,
)


class TestLogContext:
    def test_sets_and_clears_on_exit(self):
        with LogContext(correlation_id="abc", user_id="u-1"):
            assert correlation_id_context.get() == "abc"
            assert user_id_context.get() == "u-1"
        assert correlation_id_context.get() is None
        assert user_id_context.get() is None

    def test_restores_previous_value_after_nested(self):
        correlation_id_context.set("outer")
        with LogContext(correlation_id="inner"):
            assert correlation_id_context.get() == "inner"
        assert correlation_id_context.get() == "outer"

    def test_ignores_unknown_keys(self):
        with LogContext(unknown="x") as ctx:
            assert ctx._tokens == {}

    def test_coerces_value_to_string(self):
        with LogContext(user_id=42):
            assert user_id_context.get() == "42"

    def test_none_value_sets_none(self):
        correlation_id_context.set("prev")
        with LogContext(correlation_id=None):
            assert correlation_id_context.get() is None
        assert correlation_id_context.get() == "prev"


class TestSnapshotContext:
    def test_returns_only_non_null_values(self):
        with LogContext(correlation_id="c", note_id="n"):
            snap = snapshot_context()
        assert snap == {"correlation_id": "c", "note_id": "n"}

    def test_empty_when_clear(self):
        clear_context()
        assert snapshot_context() == {}


class TestHelpers:
    def test_get_correlation_id_returns_current(self):
        with LogContext(correlation_id="x"):
            assert get_correlation_id() == "x"

    def test_get_trace_id_returns_current(self):
        with LogContext(trace_id="t"):
            assert get_trace_id() == "t"

    def test_set_context_returns_none_for_unknown(self):
        assert set_context("foo", "bar") is None

    def test_log_context_decorator_form(self):
        with log_context(correlation_id="cid"):
            assert correlation_id_context.get() == "cid"
        assert correlation_id_context.get() is None

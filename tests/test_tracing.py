from __future__ import annotations

from innovanote_observability.tracing import (
    _is_enabled,
    configure_xray,
    get_current_trace_id,
    xray_subsegment,
    xray_trace,
)


class TestIsEnabled:
    def test_disabled_by_default(self, monkeypatch):
        monkeypatch.delenv("XRAY_ENABLED", raising=False)
        assert _is_enabled() is False

    def test_disabled_when_env_false(self, monkeypatch):
        monkeypatch.setenv("XRAY_ENABLED", "false")
        assert _is_enabled() is False


class TestNoOpWhenDisabled:
    def test_decorator_passthrough(self, monkeypatch):
        monkeypatch.delenv("XRAY_ENABLED", raising=False)

        @xray_trace("op")
        def f(x):
            return x * 2

        assert f(3) == 6

    def test_context_manager_passthrough(self, monkeypatch):
        monkeypatch.delenv("XRAY_ENABLED", raising=False)
        with xray_subsegment("seg"):
            pass

    def test_configure_returns_false_when_disabled(self, monkeypatch):
        monkeypatch.delenv("XRAY_ENABLED", raising=False)
        assert configure_xray() is False

    def test_get_trace_id_falls_back_to_context(self, monkeypatch):
        monkeypatch.delenv("XRAY_ENABLED", raising=False)
        from innovanote_observability.logging_context import LogContext
        with LogContext(trace_id="from-ctx"):
            assert get_current_trace_id() == "from-ctx"

from __future__ import annotations

import json

import pytest

from innovanote_observability.metrics import (
    emit_llm_metrics,
    emit_metric,
    emit_metrics,
)


def _last_payload(buffer) -> dict:
    return json.loads(buffer.getvalue().strip().splitlines()[-1])


class TestEmitMetric:
    def test_basic_metric_has_emf_envelope(self, capture_json_logs):
        emit_metric("latency", 123.4, "Milliseconds")
        payload = _last_payload(capture_json_logs)
        assert payload["latency"] == 123.4
        cw = payload["_aws"]["CloudWatchMetrics"][0]
        assert cw["Metrics"][0] == {"Name": "latency", "Unit": "Milliseconds"}
        assert cw["Namespace"] == "InnovaNote"

    def test_dimensions_become_payload_keys(self, capture_json_logs):
        emit_metric("count", 1, "Count", dimensions={"queue": "q1", "service": "front_api"})
        payload = _last_payload(capture_json_logs)
        assert payload["queue"] == "q1"
        assert payload["service"] == "front_api"
        cw = payload["_aws"]["CloudWatchMetrics"][0]
        assert set(cw["Dimensions"][0]) == {"queue", "service"}

    def test_non_numeric_raises(self):
        with pytest.raises(TypeError):
            emit_metric("bad", "not a number")  # type: ignore[arg-type]

    def test_emit_multiple_in_single_record(self, capture_json_logs):
        emit_metrics([
            {"name": "a", "value": 1, "unit": "Count"},
            {"name": "b", "value": 2, "unit": "Count"},
        ], dimensions={"d": "x"})
        payload = _last_payload(capture_json_logs)
        assert payload["a"] == 1
        assert payload["b"] == 2
        assert len(payload["_aws"]["CloudWatchMetrics"][0]["Metrics"]) == 2


class TestEmitLLMMetrics:
    def test_emits_canonical_set(self, capture_json_logs):
        emit_llm_metrics(
            model="gpt-4o-mini",
            provider="openai",
            tokens_input=100,
            tokens_output=50,
            cost_usd=0.0021,
            latency_ms=820.5,
            user_id="u-1",
            organization_id="org-1",
        )
        payload = _last_payload(capture_json_logs)
        names = {m["Name"] for m in payload["_aws"]["CloudWatchMetrics"][0]["Metrics"]}
        assert names == {"llm_tokens_input", "llm_tokens_output", "llm_cost_usd", "llm_latency_ms"}
        assert payload["model"] == "gpt-4o-mini"
        assert payload["user_id"] == "u-1"

"""Emissão de métricas CloudWatch via Embedded Metric Format (EMF).

CloudWatch reconhece logs JSON com a estrutura ``_aws.CloudWatchMetrics`` e
converte automaticamente os campos referenciados em métricas — sem custo de
PutMetricData. Documentação:
https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch_Embedded_Metric_Format_Specification.html
"""

from __future__ import annotations

import logging
import os
import time
from collections.abc import Iterable
from typing import Any

from innovanote_observability.log_events import LogEvent

DEFAULT_NAMESPACE = os.getenv("EMF_NAMESPACE", "InnovaNote")
_emf_logger = logging.getLogger("innovanote_observability.metrics")

Unit = str
NUMERIC = (int, float)


def emit_metric(
    name: str,
    value: int | float,
    unit: Unit = "None",
    *,
    dimensions: dict[str, str] | None = None,
    namespace: str | None = None,
    extra: dict[str, Any] | None = None,
) -> None:
    """Emite uma métrica EMF como log JSON.

    Args:
        name: nome da métrica.
        value: valor numérico.
        unit: unidade CloudWatch (``"Count"``, ``"Milliseconds"``, ``"Bytes"``,
            ``"None"``, etc.).
        dimensions: dimensões da métrica (cada combinação de dimensões vira
            uma série temporal separada).
        namespace: override do namespace (default ``EMF_NAMESPACE`` ou
            ``"InnovaNote"``).
        extra: campos adicionais a anexar ao log (não viram métrica, mas ficam
            queryáveis no Logs Insights).
    """
    emit_metrics(
        [{"name": name, "value": value, "unit": unit}],
        dimensions=dimensions,
        namespace=namespace,
        extra=extra,
    )


def emit_metrics(
    metrics: Iterable[dict[str, Any]],
    *,
    dimensions: dict[str, str] | None = None,
    namespace: str | None = None,
    extra: dict[str, Any] | None = None,
) -> None:
    """Emite múltiplas métricas em um único log record EMF."""
    metric_list = [
        {
            "Name": str(m["name"]),
            "Unit": str(m.get("unit", "None")),
        }
        for m in metrics
    ]
    payload: dict[str, Any] = {
        "_aws": {
            "Timestamp": int(time.time() * 1000),
            "CloudWatchMetrics": [
                {
                    "Namespace": namespace or DEFAULT_NAMESPACE,
                    "Dimensions": [list(dimensions.keys())] if dimensions else [[]],
                    "Metrics": metric_list,
                }
            ],
        },
    }

    if dimensions:
        for key, value in dimensions.items():
            payload[key] = str(value)

    for m in metrics:
        v = m["value"]
        if not isinstance(v, NUMERIC):
            raise TypeError(f"Metric value must be numeric, got {type(v).__name__}")
        payload[str(m["name"])] = v

    if extra:
        for key, value in extra.items():
            if key in payload:
                continue
            payload[key] = value

    payload.setdefault("event", LogEvent.METRIC_EMITTED.value)
    _emf_logger.info("metric_emitted", extra=payload)


def emit_llm_metrics(
    *,
    model: str,
    provider: str,
    tokens_input: int,
    tokens_output: int,
    cost_usd: float,
    latency_ms: float,
    user_id: str | None = None,
    organization_id: str | None = None,
) -> None:
    """Atalho para emitir o conjunto canônico de métricas LLM."""
    dimensions: dict[str, str] = {"model": model, "provider": provider}
    if user_id:
        dimensions["user_id"] = user_id
    if organization_id:
        dimensions["organization_id"] = organization_id
    emit_metrics(
        [
            {"name": "llm_tokens_input", "value": tokens_input, "unit": "Count"},
            {"name": "llm_tokens_output", "value": tokens_output, "unit": "Count"},
            {"name": "llm_cost_usd", "value": cost_usd, "unit": "None"},
            {"name": "llm_latency_ms", "value": latency_ms, "unit": "Milliseconds"},
        ],
        dimensions=dimensions,
    )


__all__ = ["DEFAULT_NAMESPACE", "emit_llm_metrics", "emit_metric", "emit_metrics"]

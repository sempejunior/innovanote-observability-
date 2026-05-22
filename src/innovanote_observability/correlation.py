"""Geração e propagação de correlation_id via HTTP e SQS."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

try:
    from ulid import ULID

    def _generate_id() -> str:
        return str(ULID())
except ImportError:
    import uuid

    def _generate_id() -> str:
        return str(uuid.uuid4())

from innovanote_observability.logging_context import (
    correlation_id_context,
    trace_id_context,
)

CORRELATION_HEADER = "X-Correlation-ID"
CORRELATION_HEADER_ALT = "X-Request-ID"
TRACE_HEADER = "X-Amzn-Trace-Id"

SQS_CORRELATION_ATTR = "correlation_id"
SQS_TRACE_ATTR = "trace_id"


def generate_correlation_id() -> str:
    """Retorna um novo identificador ULID-based (fallback uuid4)."""
    return _generate_id()


def extract_from_http_headers(headers: Mapping[str, str]) -> str | None:
    """Lê ``X-Correlation-ID`` ou ``X-Request-ID`` (case-insensitive)."""
    if not headers:
        return None
    for key, value in headers.items():
        normalized = key.lower()
        if normalized == CORRELATION_HEADER.lower() and value:
            return value
        if normalized == CORRELATION_HEADER_ALT.lower() and value:
            return value
    return None


def extract_trace_from_http_headers(headers: Mapping[str, str]) -> str | None:
    if not headers:
        return None
    for key, value in headers.items():
        if key.lower() == TRACE_HEADER.lower() and value:
            return value
    return None


def inject_into_http_response_headers(headers: dict[str, str], correlation_id: str) -> dict[str, str]:
    headers[CORRELATION_HEADER] = correlation_id
    return headers


def build_sqs_message_attributes(
    correlation_id: str | None = None,
    trace_id: str | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, dict[str, str]]:
    """Constrói o dict ``MessageAttributes`` no formato boto3 esperado pelo SQS."""
    attrs: dict[str, dict[str, str]] = {}
    cid = correlation_id or correlation_id_context.get()
    tid = trace_id or trace_id_context.get()
    if cid:
        attrs[SQS_CORRELATION_ATTR] = {"DataType": "String", "StringValue": str(cid)}
    if tid:
        attrs[SQS_TRACE_ATTR] = {"DataType": "String", "StringValue": str(tid)}
    if extra:
        for key, value in extra.items():
            if value is None:
                continue
            attrs[key] = {"DataType": "String", "StringValue": str(value)}
    return attrs


def extract_from_sqs_message(message: Mapping[str, Any]) -> dict[str, str | None]:
    """Lê correlation_id/trace_id de ``MessageAttributes`` (suporta payloads
    boto3 e SQS event records do Lambda)."""
    attrs = (
        message.get("MessageAttributes")
        or message.get("messageAttributes")
        or {}
    )
    if not isinstance(attrs, dict):
        return {"correlation_id": None, "trace_id": None}

    def _value(node: Any) -> str | None:
        if not isinstance(node, dict):
            return None
        return (
            node.get("StringValue")
            or node.get("stringValue")
            or node.get("Value")
            or node.get("value")
        )

    return {
        "correlation_id": _value(attrs.get(SQS_CORRELATION_ATTR)),
        "trace_id": _value(attrs.get(SQS_TRACE_ATTR)),
    }


def ensure_correlation_id() -> str:
    """Retorna o correlation_id corrente; gera e grava no contextvar se ausente."""
    current = correlation_id_context.get()
    if current:
        return current
    new_id = generate_correlation_id()
    correlation_id_context.set(new_id)
    return new_id


__all__ = [
    "CORRELATION_HEADER",
    "CORRELATION_HEADER_ALT",
    "SQS_CORRELATION_ATTR",
    "SQS_TRACE_ATTR",
    "TRACE_HEADER",
    "build_sqs_message_attributes",
    "ensure_correlation_id",
    "extract_from_http_headers",
    "extract_from_sqs_message",
    "extract_trace_from_http_headers",
    "generate_correlation_id",
    "inject_into_http_response_headers",
]

"""Helpers SQS que propagam correlation_id/trace_id automaticamente."""

from __future__ import annotations

import json
import logging
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from typing import Any

try:
    import boto3
    BOTO3_AVAILABLE = True
except ImportError:
    boto3 = None
    BOTO3_AVAILABLE = False

from innovanote_observability.correlation import (
    build_sqs_message_attributes,
    extract_from_sqs_message,
)
from innovanote_observability.error_codes import ErrorCode
from innovanote_observability.exceptions import SQSException
from innovanote_observability.log_events import LogEvent
from innovanote_observability.logging_context import LogContext

logger = logging.getLogger("innovanote_observability.sqs_helpers")

_default_client: Any = None


def _get_client(region_name: str | None = None) -> Any:
    if not BOTO3_AVAILABLE:
        raise ImportError(
            "innovanote_observability.sqs_helpers requires the 'aws' extra: "
            "pip install 'innovanote-observability[aws]'"
        )
    global _default_client
    if _default_client is None or region_name:
        _default_client = boto3.client("sqs", region_name=region_name)
    return _default_client


def publish(
    queue_url: str,
    payload: Any,
    *,
    correlation_id: str | None = None,
    trace_id: str | None = None,
    message_group_id: str | None = None,
    message_deduplication_id: str | None = None,
    extra_attributes: dict[str, Any] | None = None,
    client: Any = None,
    region_name: str | None = None,
) -> dict[str, Any]:
    """Publica payload em uma fila SQS injetando correlation_id/trace_id em ``MessageAttributes``.

    Args:
        queue_url: URL da fila.
        payload: dict serializável JSON ou string.
        correlation_id/trace_id: override (default = LogContext atual).
        message_group_id/message_deduplication_id: FIFO queues.
        extra_attributes: atributos adicionais (chave -> string).
        client: boto3 client SQS pré-instanciado (opcional).
        region_name: região AWS (se ``client`` não fornecido).

    Raises:
        SQSException: se a publicação falhar.
    """
    body = payload if isinstance(payload, str) else json.dumps(payload, ensure_ascii=False, default=str)

    attributes = build_sqs_message_attributes(
        correlation_id=correlation_id,
        trace_id=trace_id,
        extra=extra_attributes,
    )

    kwargs: dict[str, Any] = {"QueueUrl": queue_url, "MessageBody": body}
    if attributes:
        kwargs["MessageAttributes"] = attributes
    if message_group_id:
        kwargs["MessageGroupId"] = message_group_id
    if message_deduplication_id:
        kwargs["MessageDeduplicationId"] = message_deduplication_id

    sqs = client or _get_client(region_name=region_name)
    try:
        response = sqs.send_message(**kwargs)
    except Exception as exc:
        logger.error(
            "Failed to publish SQS message",
            extra={
                "event": LogEvent.SQS_MESSAGE_FAILED,
                "error_code": ErrorCode.SQS_PUBLISH_FAILED.value,
                "queue_url": queue_url,
                "exception_type": type(exc).__name__,
            },
            exc_info=True,
        )
        raise SQSException(
            message=f"Failed to publish to SQS: {exc}",
            queue_url=queue_url,
            error_code=ErrorCode.SQS_PUBLISH_FAILED,
        ) from exc

    logger.info(
        "SQS message published",
        extra={
            "event": LogEvent.SQS_MESSAGE_PUBLISHED,
            "queue_url": queue_url,
            "sqs_message_id": response.get("MessageId"),
        },
    )
    return response


@contextmanager
def sqs_message_context(message: Mapping[str, Any]) -> Iterator[dict[str, str | None]]:
    """Abre LogContext com correlation_id/trace_id extraídos da mensagem SQS.

    Use ao redor do processamento de cada mensagem no consumer:

        >>> for msg in receive_messages():
        ...     with sqs_message_context(msg):
        ...         process(msg)
    """
    extracted = extract_from_sqs_message(message)
    cid = extracted.get("correlation_id")
    tid = extracted.get("trace_id")
    message_id = message.get("MessageId") or message.get("messageId")
    ctx_kwargs: dict[str, Any] = {}
    if cid:
        ctx_kwargs["correlation_id"] = cid
    if tid:
        ctx_kwargs["trace_id"] = tid
    if message_id:
        ctx_kwargs["message_id"] = message_id
    with LogContext(**ctx_kwargs):
        logger.info(
            "SQS message consumed",
            extra={
                "event": LogEvent.SQS_MESSAGE_CONSUMED,
                "sqs_message_id": message_id,
            },
        )
        yield extracted


__all__ = ["publish", "sqs_message_context"]

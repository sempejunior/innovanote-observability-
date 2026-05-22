"""Wrappers AWS X-Ray (opcionais, importam apenas se ``aws-xray-sdk`` instalado)."""

from __future__ import annotations

import functools
import os
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from typing import Any

try:
    from aws_xray_sdk.core import xray_recorder
    XRAY_AVAILABLE = True
except ImportError:
    xray_recorder = None
    XRAY_AVAILABLE = False

from innovanote_observability.logging_context import (
    snapshot_context,
    trace_id_context,
)


def _is_enabled() -> bool:
    if not XRAY_AVAILABLE:
        return False
    enabled = os.getenv("XRAY_ENABLED", "false").lower() in {"1", "true", "yes", "on"}
    return enabled


def configure_xray(
    service_name: str | None = None,
    environment: str | None = None,
    service_version: str | None = None,
    daemon_address: str | None = None,
) -> bool:
    """Configura o recorder X-Ray se o SDK estiver disponível e habilitado.

    Returns:
        ``True`` se a configuração foi aplicada; ``False`` caso contrário.
    """
    if not _is_enabled():
        return False
    try:
        xray_recorder.configure(
            context_missing="LOG_ERROR",
            plugins=("ECSPlugin", "EC2Plugin"),
            daemon_address=daemon_address or os.getenv("XRAY_DAEMON_ADDRESS", "127.0.0.1:2000"),
            use_ssl=False,
        )
        if service_name:
            xray_recorder.put_annotation("service", service_name)
        if environment:
            xray_recorder.put_annotation("environment", environment)
        if service_version:
            xray_recorder.put_annotation("version", service_version)
        return True
    except Exception:
        return False


def xray_trace(
    name: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator que envolve a função em um subsegmento X-Ray.

    Sem efeito quando ``XRAY_ENABLED`` é falso ou o SDK não está instalado.
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        subsegment_name = name or f"{func.__module__}.{func.__name__}"

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            if not _is_enabled():
                return func(*args, **kwargs)
            with xray_recorder.in_subsegment(subsegment_name) as segment:
                ctx = snapshot_context()
                if ctx:
                    segment.put_metadata("correlation", ctx)
                if metadata:
                    segment.put_metadata("custom", metadata)
                for key in ("user_id", "organization_id", "message_id", "correlation_id"):
                    if ctx.get(key):
                        segment.put_annotation(key, ctx[key])
                try:
                    result = func(*args, **kwargs)
                    segment.put_annotation("success", True)
                    return result
                except Exception as exc:
                    segment.add_exception(exc)
                    segment.put_annotation("success", False)
                    segment.put_annotation("error_type", type(exc).__name__)
                    raise

        return wrapper

    return decorator


@contextmanager
def xray_subsegment(name: str, metadata: dict[str, Any] | None = None) -> Iterator[None]:
    """Context manager para criar subsegmentos ad-hoc."""
    if not _is_enabled():
        yield
        return
    with xray_recorder.in_subsegment(name) as segment:
        ctx = snapshot_context()
        if ctx:
            segment.put_metadata("correlation", ctx)
        if metadata:
            segment.put_metadata("custom", metadata)
        yield


def add_xray_annotation(key: str, value: str | int | float | bool) -> None:
    if not _is_enabled():
        return
    try:
        sub = xray_recorder.current_subsegment()
        if sub:
            sub.put_annotation(key, value)
    except Exception:
        pass


def add_xray_metadata(key: str, value: Any) -> None:
    if not _is_enabled():
        return
    try:
        sub = xray_recorder.current_subsegment()
        if sub:
            sub.put_metadata(key, value)
    except Exception:
        pass


def get_current_trace_id() -> str | None:
    """Retorna o trace_id do segmento X-Ray atual, ou o valor do contextvar."""
    cv_value = trace_id_context.get()
    if cv_value:
        return cv_value
    if not _is_enabled():
        return None
    try:
        segment = xray_recorder.current_segment()
        if segment:
            return segment.trace_id
    except Exception:
        return None
    return None


def trace_worker(name: str | None = None) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        trace_name = name or f"worker.{func.__name__}"

        @xray_trace(name=trace_name)
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            add_xray_annotation("component", "worker")
            add_xray_annotation("function", func.__name__)
            return func(*args, **kwargs)

        return wrapper

    return decorator


def trace_rag_operation(operation_type: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @xray_trace(name=f"rag.{operation_type}")
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            add_xray_annotation("component", "rag")
            add_xray_annotation("operation_type", operation_type)
            return func(*args, **kwargs)

        return wrapper

    return decorator


__all__ = [
    "XRAY_AVAILABLE",
    "add_xray_annotation",
    "add_xray_metadata",
    "configure_xray",
    "get_current_trace_id",
    "trace_rag_operation",
    "trace_worker",
    "xray_subsegment",
    "xray_trace",
]

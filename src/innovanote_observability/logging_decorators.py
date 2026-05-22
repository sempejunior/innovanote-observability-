"""Decorators para logging automático de operações."""

from __future__ import annotations

import asyncio
import functools
import inspect
import time
from collections.abc import Callable
from typing import Any

from innovanote_observability.error_codes import (
    ErrorCode,
    RecoveryAction,
    recovery_action_for,
)
from innovanote_observability.log_events import LogEvent
from innovanote_observability.logging_config import get_logger
from innovanote_observability.logging_context import LogContext


def _resolve_logger(func: Callable[..., Any]) -> Any:
    return get_logger(func.__module__ or "innovanote")


def log_operation(
    operation: str | None = None,
    *,
    level: str = "INFO",
    include_args: bool = False,
    include_result: bool = False,
    log_exceptions: bool = True,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Loga início, fim, duração e exceções de uma função (sync ou async).

    Args:
        operation: nome lógico da operação. Default = ``f"{module}.{func}"``.
        level: nível usado nos logs de start/end ("INFO", "DEBUG", ...).
        include_args: se True, anexa os argumentos posicionais/kwargs no log
            de start (sanitizados pelo SensitiveDataFilter).
        include_result: se True e o resultado for tipo simples, anexa no log
            de end.
        log_exceptions: se True, captura e loga exceções (re-raise).
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        op_name = operation or f"{func.__module__}.{func.__qualname__}"
        logger = _resolve_logger(func)
        log_level = getattr(__import__("logging"), level.upper(), 20)

        def _start_extra(args: tuple, kwargs: dict) -> dict[str, Any]:
            extra: dict[str, Any] = {"event": LogEvent.OPERATION_STARTED, "operation": op_name}
            if include_args:
                extra["call_args"] = _safe_args(args)
                extra["call_kwargs"] = _safe_args(kwargs)
            return extra

        def _end_extra(duration_ms: float, result: Any) -> dict[str, Any]:
            extra: dict[str, Any] = {
                "event": LogEvent.OPERATION_COMPLETED,
                "operation": op_name,
                "duration_ms": round(duration_ms, 3),
            }
            if include_result and isinstance(result, (str, int, float, bool, type(None))):
                extra["result"] = result
            return extra

        def _error_extra(duration_ms: float, exc: BaseException) -> dict[str, Any]:
            error_code = getattr(exc, "error_code", None) or ErrorCode.INTERNAL_ERROR
            recovery = (
                recovery_action_for(error_code)
                if isinstance(error_code, ErrorCode)
                else RecoveryAction.NONE
            )
            return {
                "event": LogEvent.OPERATION_FAILED,
                "operation": op_name,
                "duration_ms": round(duration_ms, 3),
                "error_code": error_code.value if isinstance(error_code, ErrorCode) else str(error_code),
                "recovery_action": recovery.value,
                "exception_type": type(exc).__name__,
            }

        if asyncio.iscoroutinefunction(func):

            @functools.wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                logger.log(log_level, f"Starting {op_name}", extra=_start_extra(args, kwargs))
                start = time.perf_counter()
                try:
                    result = await func(*args, **kwargs)
                except BaseException as exc:
                    duration_ms = (time.perf_counter() - start) * 1000
                    if log_exceptions:
                        logger.error(
                            f"Failed {op_name}: {exc}",
                            extra=_error_extra(duration_ms, exc),
                            exc_info=True,
                        )
                    raise
                duration_ms = (time.perf_counter() - start) * 1000
                logger.log(log_level, f"Completed {op_name}", extra=_end_extra(duration_ms, result))
                return result

            return async_wrapper

        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            logger.log(log_level, f"Starting {op_name}", extra=_start_extra(args, kwargs))
            start = time.perf_counter()
            try:
                result = func(*args, **kwargs)
            except BaseException as exc:
                duration_ms = (time.perf_counter() - start) * 1000
                if log_exceptions:
                    logger.error(
                        f"Failed {op_name}: {exc}",
                        extra=_error_extra(duration_ms, exc),
                        exc_info=True,
                    )
                raise
            duration_ms = (time.perf_counter() - start) * 1000
            logger.log(log_level, f"Completed {op_name}", extra=_end_extra(duration_ms, result))
            return result

        return sync_wrapper

    return decorator


def log_performance(
    operation: str | None = None,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Loga apenas a duração em DEBUG. Útil em hot paths."""
    return log_operation(operation=operation, level="DEBUG", log_exceptions=False)


def log_errors(
    operation: str | None = None,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Loga somente exceções (sem start/end). Útil para handlers já barulhentos."""

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        op_name = operation or f"{func.__module__}.{func.__qualname__}"
        logger = _resolve_logger(func)

        if asyncio.iscoroutinefunction(func):

            @functools.wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                try:
                    return await func(*args, **kwargs)
                except BaseException as exc:
                    logger.error(
                        f"Error in {op_name}: {exc}",
                        extra={
                            "event": LogEvent.OPERATION_FAILED,
                            "operation": op_name,
                            "exception_type": type(exc).__name__,
                        },
                        exc_info=True,
                    )
                    raise

            return async_wrapper

        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return func(*args, **kwargs)
            except BaseException as exc:
                logger.error(
                    f"Error in {op_name}: {exc}",
                    extra={
                        "event": LogEvent.OPERATION_FAILED,
                        "operation": op_name,
                        "exception_type": type(exc).__name__,
                    },
                    exc_info=True,
                )
                raise

        return sync_wrapper

    return decorator


def with_context(**ctx: Any) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator que envolve a função em :class:`LogContext` com os kwargs fornecidos."""

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        if asyncio.iscoroutinefunction(func):

            @functools.wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                with LogContext(**ctx):
                    return await func(*args, **kwargs)

            return async_wrapper

        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            with LogContext(**ctx):
                return func(*args, **kwargs)

        return sync_wrapper

    return decorator


def _safe_args(value: Any, max_repr: int = 200) -> Any:
    try:
        if isinstance(value, dict):
            return {str(k): _safe_args(v, max_repr) for k, v in value.items()}
        if isinstance(value, (list, tuple, set)):
            return [_safe_args(v, max_repr) for v in value]
        if isinstance(value, (str, int, float, bool, type(None))):
            return value
        if inspect.isclass(value) or inspect.isfunction(value) or inspect.ismethod(value):
            return value.__name__
        text = repr(value)
        return text if len(text) <= max_repr else text[:max_repr] + "..."
    except Exception:
        return "<unrepr>"


__all__ = ["log_errors", "log_operation", "log_performance", "with_context"]

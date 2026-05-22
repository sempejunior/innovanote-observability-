"""High-level decorators que combinam logging + tracing + auto-config.

São os pontos de entrada recomendados (``@observed``, ``@sqs_message_handler``).
A API low-level (``@log_operation`` + ``@xray_trace`` + ``sqs_message_context``)
continua disponível para casos avançados.
"""

from __future__ import annotations

import asyncio
import functools
from collections.abc import Callable
from typing import Any, overload

from innovanote_observability.logging_config import ensure_configured
from innovanote_observability.logging_decorators import log_operation
from innovanote_observability.sqs_helpers import sqs_message_context
from innovanote_observability.tracing import xray_trace


def _compose_observed(
    operation: str | None,
    level: str,
    include_args: bool,
    include_result: bool,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        ensure_configured()
        op_name = operation or f"{func.__module__}.{func.__qualname__}"
        traced = xray_trace(name=op_name)(func)
        logged = log_operation(
            operation=op_name,
            level=level,
            include_args=include_args,
            include_result=include_result,
            log_exceptions=True,
        )(traced)
        return logged

    return decorator


@overload
def observed(func: Callable[..., Any]) -> Callable[..., Any]: ...
@overload
def observed(
    *,
    operation: str | None = None,
    level: str = "INFO",
    include_args: bool = False,
    include_result: bool = False,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]: ...


def observed(
    func: Callable[..., Any] | None = None,
    *,
    operation: str | None = None,
    level: str = "INFO",
    include_args: bool = False,
    include_result: bool = False,
) -> Any:
    """Decorator universal: logging estruturado + X-Ray subsegment + auto-config.

    Pode ser usado como ``@observed`` (sem parênteses) ou
    ``@observed(operation="custom_name", include_args=True)``. Funciona em
    funções sync e async.

    Equivalente a aplicar manualmente ``@log_operation`` + ``@xray_trace``,
    mas com auto-config lazy do logging — não exige chamada prévia a
    :func:`configure_logging`.
    """
    decorator = _compose_observed(
        operation=operation,
        level=level,
        include_args=include_args,
        include_result=include_result,
    )
    if func is not None and callable(func):
        return decorator(func)
    return decorator


@overload
def sqs_message_handler(func: Callable[..., Any]) -> Callable[..., Any]: ...
@overload
def sqs_message_handler(
    *,
    operation: str | None = None,
    message_arg: int = 0,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]: ...


def sqs_message_handler(
    func: Callable[..., Any] | None = None,
    *,
    operation: str | None = None,
    message_arg: int = 0,
) -> Any:
    """Decorator para handlers de mensagens SQS.

    Abre :func:`sqs_message_context` em volta da chamada (lê
    ``correlation_id``/``trace_id``/``message_id`` dos ``MessageAttributes``),
    cria subsegmento X-Ray, loga start/end/erros e re-lança exceções para o
    consumer decidir retry/DLQ.

    O argumento ``message_arg`` indica a posição do parâmetro que contém a
    mensagem SQS (default 0 — primeiro argumento posicional).

    Example:
        >>> @sqs_message_handler
        ... def process(message: dict) -> None:
        ...     # logs do interior já vêm com correlation_id da mensagem
        ...     ...
    """

    def decorator(inner: Callable[..., Any]) -> Callable[..., Any]:
        ensure_configured()
        op_name = operation or f"sqs.{inner.__module__}.{inner.__qualname__}"
        observed_inner = observed(operation=op_name)(inner)

        def _resolve_message(args: tuple, kwargs: dict) -> dict[str, Any]:
            if "message" in kwargs:
                msg = kwargs["message"]
            elif len(args) > message_arg:
                msg = args[message_arg]
            else:
                raise ValueError(
                    f"sqs_message_handler could not find SQS message in args/kwargs "
                    f"(expected position {message_arg})"
                )
            if not isinstance(msg, dict):
                raise TypeError(
                    f"sqs_message_handler expected dict-like SQS message, got {type(msg).__name__}"
                )
            return msg

        if asyncio.iscoroutinefunction(inner):

            @functools.wraps(inner)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                msg = _resolve_message(args, kwargs)
                with sqs_message_context(msg):
                    return await observed_inner(*args, **kwargs)

            return async_wrapper

        @functools.wraps(inner)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            msg = _resolve_message(args, kwargs)
            with sqs_message_context(msg):
                return observed_inner(*args, **kwargs)

        return sync_wrapper

    if func is not None and callable(func):
        return decorator(func)
    return decorator


__all__ = ["observed", "sqs_message_handler"]

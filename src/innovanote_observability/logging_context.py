"""Context variables canônicos para enriquecimento automático de logs.

Todo log emitido por qualquer serviço InnovaNote deve carregar os mesmos campos
contextuais quando disponíveis. Os ContextVars aqui declarados são lidos pelo
:class:`RequestContextFilter` (em :mod:`.logging_filters`) e injetados em cada
log record sem necessidade de passar manualmente via ``extra={...}``.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar, Token
from typing import Any

correlation_id_context: ContextVar[str | None] = ContextVar("correlation_id", default=None)
trace_id_context: ContextVar[str | None] = ContextVar("trace_id", default=None)
user_id_context: ContextVar[str | None] = ContextVar("user_id", default=None)
organization_id_context: ContextVar[str | None] = ContextVar("organization_id", default=None)
request_method_context: ContextVar[str | None] = ContextVar("request_method", default=None)
request_path_context: ContextVar[str | None] = ContextVar("request_path", default=None)
recording_id_context: ContextVar[str | None] = ContextVar("recording_id", default=None)
transcription_id_context: ContextVar[str | None] = ContextVar("transcription_id", default=None)
note_id_context: ContextVar[str | None] = ContextVar("note_id", default=None)
notebook_id_context: ContextVar[str | None] = ContextVar("notebook_id", default=None)
automation_id_context: ContextVar[str | None] = ContextVar("automation_id", default=None)
message_id_context: ContextVar[str | None] = ContextVar("message_id", default=None)

_CONTEXT_VARS: dict[str, ContextVar[str | None]] = {
    "correlation_id": correlation_id_context,
    "trace_id": trace_id_context,
    "user_id": user_id_context,
    "organization_id": organization_id_context,
    "request_method": request_method_context,
    "request_path": request_path_context,
    "recording_id": recording_id_context,
    "transcription_id": transcription_id_context,
    "note_id": note_id_context,
    "notebook_id": notebook_id_context,
    "automation_id": automation_id_context,
    "message_id": message_id_context,
}


def get_context_var(name: str) -> ContextVar[str | None] | None:
    return _CONTEXT_VARS.get(name)


def snapshot_context() -> dict[str, str]:
    """Retorna o snapshot atual dos contextvars não-nulos."""
    return {name: cv.get() for name, cv in _CONTEXT_VARS.items() if cv.get() is not None}


def set_context(name: str, value: Any) -> Token[str | None] | None:
    cv = _CONTEXT_VARS.get(name)
    if cv is None:
        return None
    return cv.set(None if value is None else str(value))


def clear_context() -> None:
    for cv in _CONTEXT_VARS.values():
        cv.set(None)


def get_correlation_id() -> str | None:
    return correlation_id_context.get()


def get_trace_id() -> str | None:
    return trace_id_context.get()


class LogContext:
    """Context manager que injeta múltiplos contextvars de forma segura.

    Faz push dos valores informados ao entrar e reverte para os valores
    anteriores ao sair, mesmo em caso de exceção.

    Example:
        >>> with LogContext(correlation_id="01J...", user_id="u_42"):
        ...     logger.info("hello")
    """

    def __init__(self, **kwargs: Any) -> None:
        self._kwargs = kwargs
        self._tokens: dict[str, Token[str | None]] = {}

    def __enter__(self) -> LogContext:
        for key, value in self._kwargs.items():
            cv = _CONTEXT_VARS.get(key)
            if cv is None:
                continue
            self._tokens[key] = cv.set(None if value is None else str(value))
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        for key, token in self._tokens.items():
            cv = _CONTEXT_VARS[key]
            cv.reset(token)
        self._tokens.clear()


@contextmanager
def log_context(**kwargs: Any) -> Iterator[None]:
    """Equivalente funcional de :class:`LogContext` para uso com ``@contextmanager``."""
    with LogContext(**kwargs):
        yield


__all__ = [
    "LogContext",
    "clear_context",
    "correlation_id_context",
    "get_context_var",
    "get_correlation_id",
    "get_trace_id",
    "log_context",
    "set_context",
    "snapshot_context",
    "trace_id_context",
    "user_id_context",
    "organization_id_context",
    "request_method_context",
    "request_path_context",
    "recording_id_context",
    "transcription_id_context",
    "note_id_context",
    "notebook_id_context",
    "automation_id_context",
    "message_id_context",
]

"""Filtros logging que enriquecem records com contexto e sanitizam dados sensíveis."""

from __future__ import annotations

import logging
import os
import re
from typing import Any

from innovanote_observability.logging_context import _CONTEXT_VARS

SERVICE_NAME = os.getenv("NAME_MICROSERVICE") or os.getenv("SERVICE_NAME") or "unknown-service"
SERVICE_VERSION = os.getenv("SERVICE_VERSION", "0.0.0")
ENVIRONMENT = (
    os.getenv("APP_ENV")
    or os.getenv("ENVIRONMENT")
    or os.getenv("ENV")
    or "unknown"
)

_SENSITIVE_KEYS = {
    "authorization",
    "cookie",
    "set-cookie",
    "password",
    "passwd",
    "secret",
    "token",
    "api_key",
    "apikey",
    "access_token",
    "refresh_token",
    "id_token",
    "database_url",
    "client_secret",
    "private_key",
    "aws_secret_access_key",
}

_URL_PASSWORD_RE = re.compile(r"([a-zA-Z][a-zA-Z0-9+.-]*://[^:\s/@]+:)([^@\s]+)(@)")
_ASSIGNMENT_SECRET_RE = re.compile(
    r"(?i)\b(password|passwd|secret|token|api[_-]?key|client_secret|database_url|access_token|refresh_token)=([^,\s&]+)"
)
_BEARER_RE = re.compile(r"(?i)(bearer\s+)([A-Za-z0-9._\-+/=]+)")
_JWT_RE = re.compile(r"\beyJ[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+\b")


def _is_sensitive_key(key: str) -> bool:
    normalized = key.lower().replace("-", "_")
    return normalized in _SENSITIVE_KEYS or any(part in normalized for part in _SENSITIVE_KEYS)


def redact_value(value: Any, key: str | None = None) -> Any:
    """Sanitiza recursivamente strings/dicts/lists removendo segredos comuns."""
    if key and _is_sensitive_key(key):
        return "[REDACTED]"
    if isinstance(value, str):
        value = _URL_PASSWORD_RE.sub(r"\1[REDACTED]\3", value)
        value = _BEARER_RE.sub(lambda m: f"{m.group(1)}[REDACTED]", value)
        value = _JWT_RE.sub("[JWT_REDACTED]", value)
        return _ASSIGNMENT_SECRET_RE.sub(lambda m: f"{m.group(1)}=[REDACTED]", value)
    if isinstance(value, dict):
        return {str(k): redact_value(v, str(k)) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [redact_value(item) for item in value]
    return value


class RequestContextFilter(logging.Filter):
    """Injeta service/environment/version + contextvars no log record."""

    def __init__(
        self,
        service_name: str | None = None,
        environment: str | None = None,
        service_version: str | None = None,
    ) -> None:
        super().__init__()
        self.service_name = service_name or SERVICE_NAME
        self.environment = environment or ENVIRONMENT
        self.service_version = service_version or SERVICE_VERSION

    def filter(self, record: logging.LogRecord) -> bool:
        record.service = getattr(record, "service", None) or self.service_name
        record.environment = getattr(record, "environment", None) or self.environment
        record.version = getattr(record, "version", None) or self.service_version
        for name, cv in _CONTEXT_VARS.items():
            current = getattr(record, name, None)
            if current is None:
                current = cv.get()
            if current is not None:
                setattr(record, name, current)
        return True


class SensitiveDataFilter(logging.Filter):
    """Aplica :func:`redact_value` em ``record.msg`` e ``record.args``.

    O ``JsonLogFormatter`` já aplica sanitização no payload final; este filtro é
    útil para handlers de texto plano e para logs que escapam do formatter.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = redact_value(record.msg)
        if isinstance(record.args, dict):
            record.args = redact_value(record.args)
        elif isinstance(record.args, tuple):
            record.args = tuple(redact_value(a) for a in record.args)
        return True


__all__ = [
    "ENVIRONMENT",
    "RequestContextFilter",
    "SERVICE_NAME",
    "SERVICE_VERSION",
    "SensitiveDataFilter",
    "redact_value",
]

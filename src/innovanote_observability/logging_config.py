"""Setup central de logging em JSON para todos os microserviços InnovaNote."""

from __future__ import annotations

import json
import logging
import os
import traceback
from datetime import datetime, timezone
from logging.config import dictConfig
from typing import Any

from innovanote_observability.logging_filters import (
    ENVIRONMENT,
    SERVICE_NAME,
    SERVICE_VERSION,
    RequestContextFilter,
    SensitiveDataFilter,
    redact_value,
)

_RESERVED_LOG_ATTRS = {
    "args",
    "asctime",
    "created",
    "exc_info",
    "exc_text",
    "filename",
    "funcName",
    "levelname",
    "levelno",
    "lineno",
    "module",
    "msecs",
    "message",
    "msg",
    "name",
    "pathname",
    "process",
    "processName",
    "relativeCreated",
    "stack_info",
    "taskName",
    "thread",
    "threadName",
}

_BASE_CONTEXT_KEYS = (
    "service",
    "environment",
    "version",
    "correlation_id",
    "trace_id",
    "user_id",
    "organization_id",
    "request_method",
    "request_path",
    "recording_id",
    "transcription_id",
    "note_id",
    "notebook_id",
    "automation_id",
    "message_id",
)


class JsonLogFormatter(logging.Formatter):
    """Serializa o log record como JSON com os campos canônicos InnovaNote."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "service": getattr(record, "service", SERVICE_NAME),
            "environment": getattr(record, "environment", ENVIRONMENT),
            "version": getattr(record, "version", SERVICE_VERSION),
            "message": redact_value(record.getMessage()),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        for field in _BASE_CONTEXT_KEYS:
            if field in {"service", "environment", "version"}:
                continue
            value = getattr(record, field, None)
            if value is not None:
                payload[field] = redact_value(value, field)

        for key, value in record.__dict__.items():
            if key in _RESERVED_LOG_ATTRS or key in payload:
                continue
            if key.startswith("_") and key != "_aws":
                continue
            if key in _BASE_CONTEXT_KEYS:
                continue
            payload[key] = value if key == "_aws" else redact_value(value, key)

        if record.exc_info:
            payload["exception"] = redact_value("".join(traceback.format_exception(*record.exc_info)))
        if record.stack_info:
            payload["stack"] = redact_value(record.stack_info)

        return json.dumps(payload, ensure_ascii=False, default=str)


_DEFAULT_QUIET_LOGGERS = {
    "uvicorn.access": "WARNING",
    "boto3": "WARNING",
    "botocore": "WARNING",
    "s3transfer": "WARNING",
    "urllib3": "WARNING",
    "asyncio": "WARNING",
}


def build_dict_config(
    *,
    service_name: str | None = None,
    environment: str | None = None,
    service_version: str | None = None,
    log_level: str | None = None,
    extra_loggers: dict[str, str] | None = None,
) -> dict[str, Any]:
    level = (log_level or os.getenv("LOG_LEVEL", "INFO")).upper()
    loggers: dict[str, dict[str, Any]] = {
        name: {"level": lvl, "propagate": True} for name, lvl in _DEFAULT_QUIET_LOGGERS.items()
    }
    if extra_loggers:
        for name, lvl in extra_loggers.items():
            loggers[name] = {"level": lvl, "propagate": True}

    return {
        "version": 1,
        "disable_existing_loggers": False,
        "filters": {
            "request_context": {
                "()": RequestContextFilter,
                "service_name": service_name,
                "environment": environment,
                "service_version": service_version,
            },
            "sensitive": {"()": SensitiveDataFilter},
        },
        "formatters": {
            "json": {"()": JsonLogFormatter},
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "json",
                "filters": ["sensitive", "request_context"],
            },
        },
        "root": {
            "handlers": ["console"],
            "level": level,
        },
        "loggers": loggers,
    }


_configured: bool = False


def is_configured() -> bool:
    """Retorna True se :func:`configure_logging` (ou auto-config) já rodou."""
    return _configured


def configure_logging(
    *,
    service_name: str | None = None,
    environment: str | None = None,
    service_version: str | None = None,
    log_level: str | None = None,
    extra_loggers: dict[str, str] | None = None,
) -> None:
    """Configura o root logger global com JSON + filtros padronizados.

    Pode ser chamada várias vezes; cada chamada re-aplica o dictConfig.
    Em geral, prefira deixar a auto-config lazy de :func:`get_logger` cuidar
    disso lendo env vars.
    """
    global _configured
    dictConfig(
        build_dict_config(
            service_name=service_name,
            environment=environment,
            service_version=service_version,
            log_level=log_level,
            extra_loggers=extra_loggers,
        )
    )
    _configured = True


def ensure_configured() -> None:
    """Chama :func:`configure_logging` se ainda não foi chamada.

    Lê env vars padrão (``NAME_MICROSERVICE``/``SERVICE_NAME``,
    ``ENVIRONMENT``/``APP_ENV``, ``SERVICE_VERSION``, ``LOG_LEVEL``).
    Seguro chamar de várias threads — idempotente após o primeiro setup.
    """
    if not _configured:
        configure_logging()


def get_logger(name: str) -> logging.Logger:
    """Retorna um logger configurado, fazendo auto-config lazy se necessário."""
    ensure_configured()
    return logging.getLogger(name)


__all__ = [
    "JsonLogFormatter",
    "build_dict_config",
    "configure_logging",
    "ensure_configured",
    "get_logger",
    "is_configured",
]

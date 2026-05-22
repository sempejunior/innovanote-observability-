"""Middleware FastAPI + exception handlers padronizados.

Requer as dependências opcionais ``fastapi`` e ``starlette``.
"""

from __future__ import annotations

import logging
import time
from collections.abc import Awaitable, Callable
from typing import Any

try:
    from fastapi import FastAPI, HTTPException, Request
    from fastapi.exceptions import RequestValidationError
    from starlette.exceptions import HTTPException as StarletteHTTPException
    from starlette.middleware.base import BaseHTTPMiddleware
    from starlette.responses import JSONResponse, Response
except ImportError as exc:
    raise ImportError(
        "innovanote_observability.middleware_fastapi requires the 'fastapi' extra: "
        "pip install 'innovanote-observability[fastapi]'"
    ) from exc

from innovanote_observability.correlation import (
    CORRELATION_HEADER,
    ensure_correlation_id,
    extract_from_http_headers,
    extract_trace_from_http_headers,
    generate_correlation_id,
)
from innovanote_observability.error_codes import (
    ErrorCode,
    default_message_for,
)
from innovanote_observability.exceptions import AppException
from innovanote_observability.log_events import LogEvent
from innovanote_observability.logging_context import (
    LogContext,
)

_STATUS_TO_DEFAULT_CODE: dict[int, ErrorCode] = {
    400: ErrorCode.BAD_REQUEST,
    401: ErrorCode.AUTH_NOT_AUTHENTICATED,
    402: ErrorCode.BILLING_INSUFFICIENT_CREDITS,
    403: ErrorCode.AUTH_FORBIDDEN,
    404: ErrorCode.NOT_FOUND,
    405: ErrorCode.BAD_REQUEST,
    409: ErrorCode.CONFLICT,
    410: ErrorCode.NOT_FOUND,
    422: ErrorCode.VALIDATION_ERROR,
    500: ErrorCode.INTERNAL_ERROR,
    503: ErrorCode.SERVICE_UNAVAILABLE,
}

logger = logging.getLogger("innovanote_observability.middleware")


class CorrelationMiddleware(BaseHTTPMiddleware):
    """Extrai/gera correlation_id, abre LogContext e loga timing da requisição."""

    def __init__(self, app: Any, *, log_health_at_debug: bool = True) -> None:
        super().__init__(app)
        self.log_health_at_debug = log_health_at_debug

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        correlation_id = extract_from_http_headers(request.headers) or generate_correlation_id()
        trace_id = extract_trace_from_http_headers(request.headers)
        organization_id = request.headers.get("X-Organization-Context")

        request.state.correlation_id = correlation_id

        start = time.perf_counter()
        response: Response | None = None

        ctx_kwargs: dict[str, Any] = {
            "correlation_id": correlation_id,
            "request_method": request.method,
            "request_path": request.url.path,
        }
        if trace_id:
            ctx_kwargs["trace_id"] = trace_id
        if organization_id:
            ctx_kwargs["organization_id"] = organization_id

        with LogContext(**ctx_kwargs):
            try:
                response = await call_next(request)
                response.headers[CORRELATION_HEADER] = correlation_id
                return response
            finally:
                elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
                status_code = response.status_code if response is not None else 500
                is_health = request.url.path.endswith("/health") or request.url.path.endswith("/ready")
                log_level = logging.DEBUG if (is_health and self.log_health_at_debug) else logging.INFO
                logger.log(
                    log_level,
                    "http_request",
                    extra={
                        "event": LogEvent.HTTP_REQUEST,
                        "method": request.method,
                        "path": request.url.path,
                        "status_code": status_code,
                        "latency_ms": elapsed_ms,
                        "client_ip": request.client.host if request.client else None,
                        "user_agent": request.headers.get("user-agent"),
                    },
                )


def _correlation_from_request(request: Request) -> str:
    state = getattr(request.state, "correlation_id", None)
    if state:
        return state
    header = extract_from_http_headers(request.headers)
    return header or ensure_correlation_id()


def _build_error_response(
    *,
    status: int,
    code: str,
    message: str,
    correlation_id: str,
    details: dict[str, Any] | None = None,
) -> JSONResponse:
    payload = {
        "error": {
            "code": code,
            "message": message,
            "status": status,
            "details": details,
            "correlation_id": correlation_id,
        },
        "detail": message,
    }
    return JSONResponse(
        status_code=status,
        content=payload,
        headers={CORRELATION_HEADER: correlation_id},
    )


def _coerce_legacy_detail(
    detail: Any, status: int
) -> tuple[str, str, dict[str, Any] | None]:
    fallback_code = _STATUS_TO_DEFAULT_CODE.get(status, ErrorCode.INTERNAL_ERROR).value
    fallback_message = default_message_for(_STATUS_TO_DEFAULT_CODE.get(status, ErrorCode.INTERNAL_ERROR))
    if isinstance(detail, str):
        return fallback_code, detail or fallback_message, None
    if isinstance(detail, dict):
        code = str(detail.get("error_code") or detail.get("code") or fallback_code)
        message = str(detail.get("message") or detail.get("detail") or fallback_message)
        details = {
            k: v
            for k, v in detail.items()
            if k not in {"error_code", "code", "message", "detail"}
        }
        return code, message, details or None
    return fallback_code, fallback_message, None


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    cid = _correlation_from_request(request)
    code = exc.code_str()
    logger.warning(
        "AppException raised",
        extra={
            "event": LogEvent.HTTP_REQUEST_FAILED,
            "error_code": code,
            "status_code": exc.status_code,
            "path": str(request.url.path),
            "details": exc.details,
        },
    )
    return _build_error_response(
        status=exc.status_code,
        code=code,
        message=exc.message,
        correlation_id=cid,
        details=exc.details,
    )


async def http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    cid = _correlation_from_request(request)
    code, message, details = _coerce_legacy_detail(exc.detail, exc.status_code)
    logger.warning(
        "HTTPException raised",
        extra={
            "event": LogEvent.HTTP_REQUEST_FAILED,
            "error_code": code,
            "status_code": exc.status_code,
            "path": str(request.url.path),
        },
    )
    return _build_error_response(
        status=exc.status_code,
        code=code,
        message=message,
        correlation_id=cid,
        details=details,
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    cid = _correlation_from_request(request)
    fields = [
        {"loc": list(err.get("loc", [])), "msg": err.get("msg"), "type": err.get("type")}
        for err in exc.errors()
    ]
    logger.warning(
        "RequestValidationError",
        extra={
            "event": LogEvent.HTTP_REQUEST_FAILED,
            "error_code": ErrorCode.VALIDATION_ERROR.value,
            "status_code": 422,
            "path": str(request.url.path),
            "fields": fields,
        },
    )
    return _build_error_response(
        status=422,
        code=ErrorCode.VALIDATION_ERROR.value,
        message=default_message_for(ErrorCode.VALIDATION_ERROR),
        correlation_id=cid,
        details={"fields": fields},
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    cid = _correlation_from_request(request)
    logger.error(
        "Unhandled exception",
        exc_info=exc,
        extra={
            "event": LogEvent.HTTP_REQUEST_FAILED,
            "error_code": ErrorCode.INTERNAL_ERROR.value,
            "status_code": 500,
            "path": str(request.url.path),
        },
    )
    return _build_error_response(
        status=500,
        code=ErrorCode.INTERNAL_ERROR.value,
        message=default_message_for(ErrorCode.INTERNAL_ERROR),
        correlation_id=cid,
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Registra todos os handlers padronizados. Ordem: mais específico primeiro."""
    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)


def instrument(
    app: FastAPI,
    *,
    service_name: str | None = None,
    environment: str | None = None,
    service_version: str | None = None,
    log_level: str | None = None,
    enable_xray: bool | None = None,
    add_health_routes: bool = True,
    health_path: str = "/health",
    ready_path: str = "/ready",
) -> FastAPI:
    """Instrumentação one-shot de um app FastAPI.

    Executa de uma vez:

    1. ``configure_logging`` (JSON + filtros + contextvars).
    2. ``app.add_middleware(CorrelationMiddleware)``.
    3. ``register_exception_handlers(app)``.
    4. Opcionalmente, configura AWS X-Ray (se ``aws-xray-sdk`` instalado e
       ``XRAY_ENABLED`` env var "true").
    5. Opcionalmente, registra rotas ``GET /health`` e ``GET /ready``.

    Args:
        app: instância FastAPI.
        service_name/environment/service_version/log_level: override de env vars.
        enable_xray: força liga/desliga X-Ray. ``None`` = decide pela env var.
        add_health_routes: se True, registra ``/health`` e ``/ready``.
        health_path/ready_path: caminhos customizáveis.

    Returns:
        O mesmo ``app`` (permite chain).

    Example:
        >>> from fastapi import FastAPI
        >>> from innovanote_observability import instrument
        >>> app = FastAPI()
        >>> instrument(app, service_name="front-api")
    """
    from innovanote_observability.logging_config import configure_logging
    from innovanote_observability.tracing import configure_xray

    configure_logging(
        service_name=service_name,
        environment=environment,
        service_version=service_version,
        log_level=log_level,
    )
    app.add_middleware(CorrelationMiddleware)
    register_exception_handlers(app)

    if enable_xray is None or enable_xray:
        configure_xray(
            service_name=service_name,
            environment=environment,
            service_version=service_version,
        )

    if add_health_routes:
        async def _health() -> dict[str, str]:
            return {"status": "ok"}

        async def _ready() -> dict[str, str]:
            return {"status": "ready"}

        app.add_api_route(health_path, _health, methods=["GET"], include_in_schema=False)
        app.add_api_route(ready_path, _ready, methods=["GET"], include_in_schema=False)

    return app


__all__ = [
    "CorrelationMiddleware",
    "app_exception_handler",
    "http_exception_handler",
    "instrument",
    "register_exception_handlers",
    "unhandled_exception_handler",
    "validation_exception_handler",
]

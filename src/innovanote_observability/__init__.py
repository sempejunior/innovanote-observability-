"""innovanote-observability — biblioteca compartilhada de observabilidade.

API pública estável a partir de v0.1.0. Mudanças que quebrem este export
exigem bump de major version.
"""

from innovanote_observability.correlation import (
    CORRELATION_HEADER,
    build_sqs_message_attributes,
    ensure_correlation_id,
    extract_from_http_headers,
    extract_from_sqs_message,
    generate_correlation_id,
)
from innovanote_observability.error_codes import (
    DEFAULT_MESSAGE_BY_CODE,
    DEFAULT_RECOVERY_BY_CODE,
    DEFAULT_STATUS_BY_CODE,
    ErrorCode,
    RecoveryAction,
    default_message_for,
    recovery_action_for,
    status_for,
)
from innovanote_observability.exceptions import (
    AppException,
    BadRequestException,
    BusinessError,
    ConflictException,
    InsufficientCreditsError,
    InternalServerErrorException,
    LLMException,
    LLMRateLimitException,
    LLMTimeoutException,
    LLMTokenLimitExceededException,
    NotFoundException,
    RAGException,
    ServiceUnavailableException,
    SQSException,
    TranscriptionError,
    ValidationException,
)
from innovanote_observability.instrumentation import (
    observed,
    sqs_message_handler,
)
from innovanote_observability.log_events import LogEvent
from innovanote_observability.logging_config import (
    JsonLogFormatter,
    configure_logging,
    ensure_configured,
    get_logger,
    is_configured,
)
from innovanote_observability.logging_context import (
    LogContext,
    clear_context,
    get_correlation_id,
    get_trace_id,
    log_context,
    set_context,
    snapshot_context,
)
from innovanote_observability.logging_decorators import (
    log_errors,
    log_operation,
    log_performance,
    with_context,
)
from innovanote_observability.logging_filters import (
    RequestContextFilter,
    SensitiveDataFilter,
    redact_value,
)
from innovanote_observability.metrics import (
    emit_llm_metrics,
    emit_metric,
    emit_metrics,
)

__version__ = "0.1.0"


def __getattr__(name: str):
    """Lazy import para `instrument` (requer extra ``[fastapi]``) e submódulo ``sqs``.

    Permite que workers sem FastAPI instalado importem o pacote sem crash.
    """
    import importlib
    import sys

    if name == "instrument":
        from innovanote_observability.middleware_fastapi import instrument as _instrument
        return _instrument
    if name == "sqs":
        module = importlib.import_module("innovanote_observability.sqs")
        sys.modules[__name__].__dict__["sqs"] = module
        return module
    raise AttributeError(f"module 'innovanote_observability' has no attribute {name!r}")

__all__ = [
    "AppException",
    "BadRequestException",
    "BusinessError",
    "CORRELATION_HEADER",
    "ConflictException",
    "DEFAULT_MESSAGE_BY_CODE",
    "DEFAULT_RECOVERY_BY_CODE",
    "DEFAULT_STATUS_BY_CODE",
    "ErrorCode",
    "InsufficientCreditsError",
    "InternalServerErrorException",
    "JsonLogFormatter",
    "LLMException",
    "LLMRateLimitException",
    "LLMTimeoutException",
    "LLMTokenLimitExceededException",
    "LogContext",
    "LogEvent",
    "NotFoundException",
    "RAGException",
    "RecoveryAction",
    "RequestContextFilter",
    "SQSException",
    "SensitiveDataFilter",
    "ServiceUnavailableException",
    "TranscriptionError",
    "ValidationException",
    "__version__",
    "build_sqs_message_attributes",
    "clear_context",
    "configure_logging",
    "default_message_for",
    "emit_llm_metrics",
    "emit_metric",
    "emit_metrics",
    "ensure_configured",
    "ensure_correlation_id",
    "extract_from_http_headers",
    "extract_from_sqs_message",
    "generate_correlation_id",
    "get_correlation_id",
    "get_logger",
    "get_trace_id",
    "instrument",
    "is_configured",
    "log_context",
    "log_errors",
    "log_operation",
    "log_performance",
    "observed",
    "recovery_action_for",
    "redact_value",
    "set_context",
    "snapshot_context",
    "sqs",
    "sqs_message_handler",
    "status_for",
    "with_context",
]

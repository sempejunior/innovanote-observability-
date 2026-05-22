"""Hierarquia de exceções compartilhada com error_code embutido."""

from __future__ import annotations

from typing import Any

from innovanote_observability.error_codes import (
    ErrorCode,
    default_message_for,
    status_for,
)


class AppException(Exception):
    """Base de toda exceção de domínio InnovaNote.

    Carrega ``error_code``, ``status_code`` e ``details`` para que o handler
    global transforme qualquer subclasse em ``ErrorResponse`` padronizado sem
    boilerplate em cada controller.
    """

    default_code: ErrorCode = ErrorCode.INTERNAL_ERROR
    default_status: int = 500

    def __init__(
        self,
        message: str | None = None,
        error_code: ErrorCode | str | None = None,
        status_code: int | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.error_code: ErrorCode | str = error_code or self.default_code
        if status_code is not None:
            self.status_code = status_code
        elif isinstance(self.error_code, ErrorCode):
            self.status_code = status_for(self.error_code)
        else:
            self.status_code = self.default_status
        if message is not None:
            self.message = message
        elif isinstance(self.error_code, ErrorCode):
            self.message = default_message_for(self.error_code)
        else:
            self.message = default_message_for(self.default_code)
        self.details: dict[str, Any] | None = details
        super().__init__(self.message)

    def code_str(self) -> str:
        return self.error_code.value if isinstance(self.error_code, ErrorCode) else str(self.error_code)


class BusinessError(AppException):
    default_code = ErrorCode.BAD_REQUEST
    default_status = 400


class NotFoundException(AppException):
    default_code = ErrorCode.NOT_FOUND
    default_status = 404


class BadRequestException(AppException):
    default_code = ErrorCode.BAD_REQUEST
    default_status = 400


class ValidationException(AppException):
    default_code = ErrorCode.VALIDATION_ERROR
    default_status = 422


class ConflictException(AppException):
    default_code = ErrorCode.CONFLICT
    default_status = 409


class InternalServerErrorException(AppException):
    default_code = ErrorCode.INTERNAL_ERROR
    default_status = 500


class ServiceUnavailableException(AppException):
    default_code = ErrorCode.SERVICE_UNAVAILABLE
    default_status = 503


class InsufficientCreditsError(AppException):
    default_code = ErrorCode.BILLING_INSUFFICIENT_CREDITS

    def __init__(
        self,
        message: str | None = None,
        credits_remaining: int = 0,
        credits_required: int = 0,
        error_code: ErrorCode | None = None,
    ) -> None:
        super().__init__(
            message=message,
            error_code=error_code,
            details={
                "credits_remaining": credits_remaining,
                "credits_required": credits_required,
            },
        )
        self.credits_remaining = credits_remaining
        self.credits_required = credits_required


class TranscriptionError(AppException):
    default_code = ErrorCode.TRANSCRIPTION_FAILED


class AudioCompressionError(AppException):
    default_code = ErrorCode.AUDIO_COMPRESSION_FAILED


class S3UploadError(AppException):
    default_code = ErrorCode.TRANSCRIPTION_UPLOAD_FAILED


class DatabaseSaveError(AppException):
    default_code = ErrorCode.INTERNAL_ERROR


class LLMException(AppException):
    default_code = ErrorCode.LLM_PROVIDER_ERROR


class LLMTimeoutException(LLMException):
    default_code = ErrorCode.LLM_TIMEOUT


class LLMRateLimitException(LLMException):
    default_code = ErrorCode.LLM_RATE_LIMIT


class LLMTokenLimitExceededException(LLMException):
    default_code = ErrorCode.LLM_TOKEN_LIMIT_EXCEEDED


class SQSException(AppException):
    default_code = ErrorCode.SQS_PUBLISH_FAILED

    def __init__(
        self,
        message: str,
        queue_url: str | None = None,
        message_id: str | None = None,
        error_code: ErrorCode | None = None,
    ) -> None:
        details: dict[str, Any] = {}
        if queue_url is not None:
            details["queue_url"] = queue_url
        if message_id is not None:
            details["message_id"] = message_id
        super().__init__(message=message, error_code=error_code, details=details or None)


class RAGException(AppException):
    default_code = ErrorCode.RAG_QUERY_FAILED


__all__ = [
    "AppException",
    "AudioCompressionError",
    "BadRequestException",
    "BusinessError",
    "ConflictException",
    "DatabaseSaveError",
    "InsufficientCreditsError",
    "InternalServerErrorException",
    "LLMException",
    "LLMRateLimitException",
    "LLMTimeoutException",
    "LLMTokenLimitExceededException",
    "NotFoundException",
    "RAGException",
    "S3UploadError",
    "SQSException",
    "ServiceUnavailableException",
    "TranscriptionError",
    "ValidationException",
]

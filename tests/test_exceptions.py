from __future__ import annotations

from innovanote_observability.error_codes import ErrorCode
from innovanote_observability.exceptions import (
    AppException,
    InsufficientCreditsError,
    LLMRateLimitException,
    LLMTimeoutException,
    NotFoundException,
    SQSException,
    ValidationException,
)


class TestAppException:
    def test_default_code_and_status(self):
        exc = AppException()
        assert exc.error_code == ErrorCode.INTERNAL_ERROR
        assert exc.status_code == 500

    def test_explicit_error_code_sets_status_from_table(self):
        exc = AppException(error_code=ErrorCode.AUTH_FORBIDDEN)
        assert exc.status_code == 403

    def test_explicit_status_override(self):
        exc = AppException(error_code=ErrorCode.AUTH_FORBIDDEN, status_code=418)
        assert exc.status_code == 418

    def test_code_str_returns_enum_value(self):
        assert AppException(error_code=ErrorCode.NOT_FOUND).code_str() == "NOT_FOUND"

    def test_message_falls_back_to_default(self):
        exc = AppException(error_code=ErrorCode.NOTE_NOT_FOUND)
        assert "Nota" in exc.message


class TestSubclasses:
    def test_not_found_exception(self):
        exc = NotFoundException(error_code=ErrorCode.NOTE_NOT_FOUND)
        assert exc.status_code == 404

    def test_validation_exception(self):
        exc = ValidationException()
        assert exc.status_code == 422
        assert exc.error_code == ErrorCode.VALIDATION_ERROR

    def test_llm_rate_limit_status_429(self):
        assert LLMRateLimitException().status_code == 429

    def test_llm_timeout_status_504(self):
        assert LLMTimeoutException().status_code == 504


class TestInsufficientCredits:
    def test_carries_credit_details(self):
        exc = InsufficientCreditsError(credits_remaining=2, credits_required=5)
        assert exc.details == {"credits_remaining": 2, "credits_required": 5}
        assert exc.status_code == 402


class TestSQSException:
    def test_details_include_queue_url(self):
        exc = SQSException("boom", queue_url="https://sqs/q1", message_id="m1")
        assert exc.details == {"queue_url": "https://sqs/q1", "message_id": "m1"}

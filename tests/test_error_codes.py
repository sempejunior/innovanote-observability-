from __future__ import annotations

from innovanote_observability.error_codes import (
    DEFAULT_MESSAGE_BY_CODE,
    DEFAULT_STATUS_BY_CODE,
    ErrorCode,
    RecoveryAction,
    default_message_for,
    recovery_action_for,
    status_for,
)


class TestErrorCode:
    def test_codes_have_string_value(self):
        for code in ErrorCode:
            assert isinstance(code.value, str)

    def test_every_code_has_status_and_message(self):
        missing_status = [c.name for c in ErrorCode if c not in DEFAULT_STATUS_BY_CODE]
        missing_msg = [c.name for c in ErrorCode if c not in DEFAULT_MESSAGE_BY_CODE]
        assert missing_status == []
        assert missing_msg == []


class TestHelpers:
    def test_status_for_known(self):
        assert status_for(ErrorCode.NOT_FOUND) == 404
        assert status_for(ErrorCode.AUTH_FORBIDDEN) == 403
        assert status_for(ErrorCode.LLM_RATE_LIMIT) == 429

    def test_default_message_in_ptbr(self):
        msg = default_message_for(ErrorCode.NOTE_NOT_FOUND)
        assert "ã" in msg or "ç" in msg or "não" in msg.lower()

    def test_recovery_action_for_cuda_oom(self):
        assert recovery_action_for(ErrorCode.CUDA_OUT_OF_MEMORY) == RecoveryAction.FALLBACK_CPU

    def test_recovery_action_default_none(self):
        assert recovery_action_for(ErrorCode.NOT_FOUND) == RecoveryAction.NONE

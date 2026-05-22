"""LogEvent canônicos InnovaNote.

Use em ``extra={"event": LogEvent.XXX}`` para padronizar queries em Logs Insights.
Convenção: nomes em snake_case, agrupados por domínio.
"""

from __future__ import annotations

from enum import Enum


class LogEvent(str, Enum):
    HTTP_REQUEST = "http_request"
    HTTP_REQUEST_FAILED = "http_request_failed"

    AUTH_LOGIN_ATTEMPT = "auth_login_attempt"
    AUTH_LOGIN_SUCCESS = "auth_login_success"
    AUTH_LOGIN_FAILED = "auth_login_failed"
    AUTH_LOGOUT = "auth_logout"
    AUTH_TOKEN_REFRESHED = "auth_token_refreshed"

    RECORDING_STARTED = "recording_started"
    RECORDING_STOPPED = "recording_stopped"
    RECORDING_CHUNK_CREATED = "recording_chunk_created"
    RECORDING_UPLOADED = "recording_uploaded"
    RECORDING_FAILED = "recording_failed"

    TRANSCRIPTION_STARTED = "transcription_started"
    TRANSCRIPTION_COMPLETE = "transcription_complete"
    TRANSCRIPTION_FAILED = "transcription_failed"
    TRANSCRIPTION_CHUNK_PROCESSED = "transcription_chunk_processed"
    DIARIZATION_STARTED = "diarization_started"
    DIARIZATION_COMPLETE = "diarization_complete"

    NOTE_CREATED = "note_created"
    NOTE_UPDATED = "note_updated"
    NOTE_DELETED = "note_deleted"
    NOTE_PERSISTED_S3 = "note_persisted_s3"

    INSIGHT_REQUESTED = "insight_requested"
    INSIGHT_GENERATED = "insight_generated"
    INSIGHT_FAILED = "insight_failed"

    AUTOMATION_TRIGGERED = "automation_triggered"
    AUTOMATION_COMPLETED = "automation_completed"
    AUTOMATION_FAILED = "automation_failed"

    LLM_CALL_STARTED = "llm_call_started"
    LLM_CALL_COMPLETE = "llm_call_complete"
    LLM_CALL_FAILED = "llm_call_failed"
    LLM_MODEL_SELECTED = "llm_model_selected"
    LLM_FALLBACK_TRIGGERED = "llm_fallback_triggered"

    RAG_INGEST_STARTED = "rag_ingest_started"
    RAG_INGEST_COMPLETE = "rag_ingest_complete"
    RAG_QUERY_STARTED = "rag_query_started"
    RAG_QUERY_COMPLETE = "rag_query_complete"

    SQS_MESSAGE_PUBLISHED = "sqs_message_published"
    SQS_MESSAGE_CONSUMED = "sqs_message_consumed"
    SQS_MESSAGE_PROCESSED = "sqs_message_processed"
    SQS_MESSAGE_FAILED = "sqs_message_failed"
    SQS_MESSAGE_DLQ = "sqs_message_dlq"

    HARDWARE_DETECTION_STARTED = "hardware_detection_started"
    HARDWARE_DETECTION_COMPLETE = "hardware_detection_complete"
    GPU_DETECTED = "gpu_detected"
    GPU_DETECTION_FAILED = "gpu_detection_failed"
    CUDA_VERSION_DETECTED = "cuda_version_detected"

    OPERATION_STARTED = "operation_started"
    OPERATION_COMPLETED = "operation_completed"
    OPERATION_FAILED = "operation_failed"

    METRIC_EMITTED = "metric_emitted"


__all__ = ["LogEvent"]

"""Enum unificado de ErrorCodes InnovaNote.

Códigos são parte do contrato público da API — nunca renomear/remover. Para
deprecar, deixar o código existente e adicionar um sucessor.

Convenção: ``<DOMAIN>_<EVENT>``, SCREAMING_SNAKE_CASE.
"""

from __future__ import annotations

from enum import Enum


class ErrorCode(str, Enum):
    AUTH_INVALID_CREDENTIALS = "AUTH_INVALID_CREDENTIALS"
    AUTH_TOKEN_EXPIRED = "AUTH_TOKEN_EXPIRED"
    AUTH_TOKEN_INVALID = "AUTH_TOKEN_INVALID"
    AUTH_NOT_AUTHENTICATED = "AUTH_NOT_AUTHENTICATED"
    AUTH_FORBIDDEN = "AUTH_FORBIDDEN"
    AUTH_ORG_ACCESS_DENIED = "AUTH_ORG_ACCESS_DENIED"

    USER_NOT_FOUND = "USER_NOT_FOUND"
    USER_ALREADY_EXISTS = "USER_ALREADY_EXISTS"
    USER_EMAIL_NOT_CONFIRMED = "USER_EMAIL_NOT_CONFIRMED"
    USER_INVALID_DATA = "USER_INVALID_DATA"

    ORGANIZATION_NOT_FOUND = "ORGANIZATION_NOT_FOUND"
    ORGANIZATION_ACCESS_DENIED = "ORGANIZATION_ACCESS_DENIED"

    INVITATION_NOT_FOUND = "INVITATION_NOT_FOUND"
    INVITATION_EXPIRED = "INVITATION_EXPIRED"
    INVITATION_ALREADY_USED = "INVITATION_ALREADY_USED"

    NOTEBOOK_NOT_FOUND = "NOTEBOOK_NOT_FOUND"
    NOTEBOOK_LIMIT_REACHED = "NOTEBOOK_LIMIT_REACHED"
    NOTEBOOK_ACCESS_DENIED = "NOTEBOOK_ACCESS_DENIED"

    SECTION_NOT_FOUND = "SECTION_NOT_FOUND"
    SECTION_ACCESS_DENIED = "SECTION_ACCESS_DENIED"

    NOTE_NOT_FOUND = "NOTE_NOT_FOUND"
    NOTE_ACCESS_DENIED = "NOTE_ACCESS_DENIED"

    TRANSCRIPTION_NOT_FOUND = "TRANSCRIPTION_NOT_FOUND"
    TRANSCRIPTION_ACCESS_DENIED = "TRANSCRIPTION_ACCESS_DENIED"
    TRANSCRIPTION_FAILED = "TRANSCRIPTION_FAILED"
    TRANSCRIPTION_UPLOAD_FAILED = "TRANSCRIPTION_UPLOAD_FAILED"
    AUDIO_DIARIZATION_FAILED = "AUDIO_DIARIZATION_FAILED"
    AUDIO_DEVICE_ERROR = "AUDIO_DEVICE_ERROR"
    AUDIO_COMPRESSION_FAILED = "AUDIO_COMPRESSION_FAILED"

    INSIGHT_NOT_FOUND = "INSIGHT_NOT_FOUND"
    INSIGHT_TYPE_NOT_FOUND = "INSIGHT_TYPE_NOT_FOUND"
    INSIGHT_GENERATION_FAILED = "INSIGHT_GENERATION_FAILED"
    INSIGHT_ACCESS_DENIED = "INSIGHT_ACCESS_DENIED"

    AUTOMATION_NOT_FOUND = "AUTOMATION_NOT_FOUND"
    AUTOMATION_INVALID_CONFIG = "AUTOMATION_INVALID_CONFIG"
    AUTOMATION_EXECUTION_FAILED = "AUTOMATION_EXECUTION_FAILED"

    LLM_TIMEOUT = "LLM_TIMEOUT"
    LLM_RATE_LIMIT = "LLM_RATE_LIMIT"
    LLM_PROVIDER_ERROR = "LLM_PROVIDER_ERROR"
    LLM_TOKEN_LIMIT_EXCEEDED = "LLM_TOKEN_LIMIT_EXCEEDED"
    LLM_INVALID_RESPONSE = "LLM_INVALID_RESPONSE"

    RAG_INGEST_FAILED = "RAG_INGEST_FAILED"
    RAG_QUERY_FAILED = "RAG_QUERY_FAILED"
    RAG_EMBEDDER_FAILED = "RAG_EMBEDDER_FAILED"

    SQS_PUBLISH_FAILED = "SQS_PUBLISH_FAILED"
    SQS_CONSUME_FAILED = "SQS_CONSUME_FAILED"
    SQS_DLQ_MESSAGE = "SQS_DLQ_MESSAGE"

    HARDWARE_DETECTION_ERROR = "HARDWARE_DETECTION_ERROR"
    GPU_INITIALIZATION_ERROR = "GPU_INITIALIZATION_ERROR"
    CUDA_COMPATIBILITY_ERROR = "CUDA_COMPATIBILITY_ERROR"
    CUDA_OUT_OF_MEMORY = "CUDA_OUT_OF_MEMORY"
    MODEL_LOAD_ERROR = "MODEL_LOAD_ERROR"

    BILLING_INSUFFICIENT_CREDITS = "BILLING_INSUFFICIENT_CREDITS"
    BILLING_PAYMENT_FAILED = "BILLING_PAYMENT_FAILED"
    BILLING_SUBSCRIPTION_NOT_FOUND = "BILLING_SUBSCRIPTION_NOT_FOUND"
    BILLING_PENDING_SUBSCRIPTION_EXISTS = "BILLING_PENDING_SUBSCRIPTION_EXISTS"
    BILLING_PLAN_NOT_FOUND = "BILLING_PLAN_NOT_FOUND"

    INTEGRATION_NOT_FOUND = "INTEGRATION_NOT_FOUND"
    INTEGRATION_INVALID_CONFIG = "INTEGRATION_INVALID_CONFIG"

    PROJECT_NOT_FOUND = "PROJECT_NOT_FOUND"
    SPRINT_NOT_FOUND = "SPRINT_NOT_FOUND"
    SPRINT_ITEM_INVALID_POLYMORPHISM = "SPRINT_ITEM_INVALID_POLYMORPHISM"
    SPRINT_ITEM_DUPLICATE = "SPRINT_ITEM_DUPLICATE"
    SPRINT_INVALID_STATUS = "SPRINT_INVALID_STATUS"
    ROADMAP_NOT_FOUND = "ROADMAP_NOT_FOUND"

    ENTITY_LINK_NOT_FOUND = "ENTITY_LINK_NOT_FOUND"
    ENTITY_LINK_INVALID_TYPES = "ENTITY_LINK_INVALID_TYPES"
    ENTITY_LINK_ALREADY_EXISTS = "ENTITY_LINK_ALREADY_EXISTS"
    ENTITY_LINK_ACCESS_DENIED = "ENTITY_LINK_ACCESS_DENIED"

    TEAM_NOT_FOUND = "TEAM_NOT_FOUND"
    TEAM_ACCESS_DENIED = "TEAM_ACCESS_DENIED"

    VALIDATION_ERROR = "VALIDATION_ERROR"
    BAD_REQUEST = "BAD_REQUEST"
    NOT_FOUND = "NOT_FOUND"
    CONFLICT = "CONFLICT"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"


class RecoveryAction(str, Enum):
    RETRY = "retry"
    RETRY_WITH_BACKOFF = "retry_with_backoff"
    FALLBACK_CPU = "fallback_cpu"
    FALLBACK_MODEL = "fallback_model"
    SEND_TO_DLQ = "send_to_dlq"
    NOTIFY_USER = "notify_user"
    REFRESH_TOKEN = "refresh_token"
    NONE = "none"


DEFAULT_STATUS_BY_CODE: dict[ErrorCode, int] = {
    ErrorCode.AUTH_INVALID_CREDENTIALS: 401,
    ErrorCode.AUTH_TOKEN_EXPIRED: 401,
    ErrorCode.AUTH_TOKEN_INVALID: 401,
    ErrorCode.AUTH_NOT_AUTHENTICATED: 401,
    ErrorCode.AUTH_FORBIDDEN: 403,
    ErrorCode.AUTH_ORG_ACCESS_DENIED: 403,
    ErrorCode.USER_NOT_FOUND: 404,
    ErrorCode.USER_ALREADY_EXISTS: 409,
    ErrorCode.USER_EMAIL_NOT_CONFIRMED: 403,
    ErrorCode.USER_INVALID_DATA: 422,
    ErrorCode.ORGANIZATION_NOT_FOUND: 404,
    ErrorCode.ORGANIZATION_ACCESS_DENIED: 403,
    ErrorCode.INVITATION_NOT_FOUND: 404,
    ErrorCode.INVITATION_EXPIRED: 410,
    ErrorCode.INVITATION_ALREADY_USED: 409,
    ErrorCode.NOTEBOOK_NOT_FOUND: 404,
    ErrorCode.NOTEBOOK_LIMIT_REACHED: 402,
    ErrorCode.NOTEBOOK_ACCESS_DENIED: 403,
    ErrorCode.SECTION_NOT_FOUND: 404,
    ErrorCode.SECTION_ACCESS_DENIED: 403,
    ErrorCode.NOTE_NOT_FOUND: 404,
    ErrorCode.NOTE_ACCESS_DENIED: 403,
    ErrorCode.TRANSCRIPTION_NOT_FOUND: 404,
    ErrorCode.TRANSCRIPTION_ACCESS_DENIED: 403,
    ErrorCode.TRANSCRIPTION_FAILED: 500,
    ErrorCode.TRANSCRIPTION_UPLOAD_FAILED: 500,
    ErrorCode.AUDIO_DIARIZATION_FAILED: 500,
    ErrorCode.AUDIO_DEVICE_ERROR: 500,
    ErrorCode.AUDIO_COMPRESSION_FAILED: 500,
    ErrorCode.INSIGHT_NOT_FOUND: 404,
    ErrorCode.INSIGHT_TYPE_NOT_FOUND: 404,
    ErrorCode.INSIGHT_GENERATION_FAILED: 500,
    ErrorCode.INSIGHT_ACCESS_DENIED: 403,
    ErrorCode.AUTOMATION_NOT_FOUND: 404,
    ErrorCode.AUTOMATION_INVALID_CONFIG: 400,
    ErrorCode.AUTOMATION_EXECUTION_FAILED: 500,
    ErrorCode.LLM_TIMEOUT: 504,
    ErrorCode.LLM_RATE_LIMIT: 429,
    ErrorCode.LLM_PROVIDER_ERROR: 502,
    ErrorCode.LLM_TOKEN_LIMIT_EXCEEDED: 413,
    ErrorCode.LLM_INVALID_RESPONSE: 502,
    ErrorCode.RAG_INGEST_FAILED: 500,
    ErrorCode.RAG_QUERY_FAILED: 500,
    ErrorCode.RAG_EMBEDDER_FAILED: 500,
    ErrorCode.SQS_PUBLISH_FAILED: 500,
    ErrorCode.SQS_CONSUME_FAILED: 500,
    ErrorCode.SQS_DLQ_MESSAGE: 500,
    ErrorCode.HARDWARE_DETECTION_ERROR: 500,
    ErrorCode.GPU_INITIALIZATION_ERROR: 500,
    ErrorCode.CUDA_COMPATIBILITY_ERROR: 500,
    ErrorCode.CUDA_OUT_OF_MEMORY: 500,
    ErrorCode.MODEL_LOAD_ERROR: 500,
    ErrorCode.BILLING_INSUFFICIENT_CREDITS: 402,
    ErrorCode.BILLING_PAYMENT_FAILED: 402,
    ErrorCode.BILLING_SUBSCRIPTION_NOT_FOUND: 404,
    ErrorCode.BILLING_PENDING_SUBSCRIPTION_EXISTS: 409,
    ErrorCode.BILLING_PLAN_NOT_FOUND: 404,
    ErrorCode.INTEGRATION_NOT_FOUND: 404,
    ErrorCode.INTEGRATION_INVALID_CONFIG: 400,
    ErrorCode.PROJECT_NOT_FOUND: 404,
    ErrorCode.SPRINT_NOT_FOUND: 404,
    ErrorCode.SPRINT_ITEM_INVALID_POLYMORPHISM: 422,
    ErrorCode.SPRINT_ITEM_DUPLICATE: 409,
    ErrorCode.SPRINT_INVALID_STATUS: 409,
    ErrorCode.ROADMAP_NOT_FOUND: 404,
    ErrorCode.ENTITY_LINK_NOT_FOUND: 404,
    ErrorCode.ENTITY_LINK_INVALID_TYPES: 422,
    ErrorCode.ENTITY_LINK_ALREADY_EXISTS: 409,
    ErrorCode.ENTITY_LINK_ACCESS_DENIED: 403,
    ErrorCode.TEAM_NOT_FOUND: 404,
    ErrorCode.TEAM_ACCESS_DENIED: 403,
    ErrorCode.VALIDATION_ERROR: 422,
    ErrorCode.BAD_REQUEST: 400,
    ErrorCode.NOT_FOUND: 404,
    ErrorCode.CONFLICT: 409,
    ErrorCode.INTERNAL_ERROR: 500,
    ErrorCode.SERVICE_UNAVAILABLE: 503,
}


DEFAULT_MESSAGE_BY_CODE: dict[ErrorCode, str] = {
    ErrorCode.AUTH_INVALID_CREDENTIALS: "Email ou senha inválidos.",
    ErrorCode.AUTH_TOKEN_EXPIRED: "Sua sessão expirou. Faça login novamente.",
    ErrorCode.AUTH_TOKEN_INVALID: "Token de autenticação inválido.",
    ErrorCode.AUTH_NOT_AUTHENTICATED: "Você precisa estar autenticado para realizar essa ação.",
    ErrorCode.AUTH_FORBIDDEN: "Você não tem permissão para realizar essa ação.",
    ErrorCode.AUTH_ORG_ACCESS_DENIED: "Você não tem acesso a essa organização.",
    ErrorCode.USER_NOT_FOUND: "Usuário não encontrado.",
    ErrorCode.USER_ALREADY_EXISTS: "Já existe um usuário com esse email.",
    ErrorCode.USER_EMAIL_NOT_CONFIRMED: "Confirme seu email antes de continuar.",
    ErrorCode.USER_INVALID_DATA: "Dados do usuário inválidos.",
    ErrorCode.ORGANIZATION_NOT_FOUND: "Organização não encontrada.",
    ErrorCode.ORGANIZATION_ACCESS_DENIED: "Você não tem acesso a essa organização.",
    ErrorCode.INVITATION_NOT_FOUND: "Convite não encontrado.",
    ErrorCode.INVITATION_EXPIRED: "Esse convite expirou.",
    ErrorCode.INVITATION_ALREADY_USED: "Esse convite já foi utilizado.",
    ErrorCode.NOTEBOOK_NOT_FOUND: "Notebook não encontrado.",
    ErrorCode.NOTEBOOK_LIMIT_REACHED: "Você atingiu o limite de notebooks do seu plano.",
    ErrorCode.NOTEBOOK_ACCESS_DENIED: "Você não tem acesso a esse notebook.",
    ErrorCode.SECTION_NOT_FOUND: "Seção não encontrada.",
    ErrorCode.SECTION_ACCESS_DENIED: "Você não tem acesso a essa seção.",
    ErrorCode.NOTE_NOT_FOUND: "Nota não encontrada.",
    ErrorCode.NOTE_ACCESS_DENIED: "Você não tem acesso a essa nota.",
    ErrorCode.TRANSCRIPTION_NOT_FOUND: "Transcrição não encontrada.",
    ErrorCode.TRANSCRIPTION_ACCESS_DENIED: "Você não tem acesso a essa transcrição.",
    ErrorCode.TRANSCRIPTION_FAILED: "Falha ao processar a transcrição.",
    ErrorCode.TRANSCRIPTION_UPLOAD_FAILED: "Falha ao enviar o áudio.",
    ErrorCode.AUDIO_DIARIZATION_FAILED: "Falha ao identificar interlocutores no áudio.",
    ErrorCode.AUDIO_DEVICE_ERROR: "Falha ao acessar o dispositivo de áudio.",
    ErrorCode.AUDIO_COMPRESSION_FAILED: "Falha ao comprimir o áudio.",
    ErrorCode.INSIGHT_NOT_FOUND: "Insight não encontrado.",
    ErrorCode.INSIGHT_TYPE_NOT_FOUND: "Tipo de insight não encontrado.",
    ErrorCode.INSIGHT_GENERATION_FAILED: "Falha ao gerar o insight.",
    ErrorCode.INSIGHT_ACCESS_DENIED: "Você não tem acesso a esse insight.",
    ErrorCode.AUTOMATION_NOT_FOUND: "Automação não encontrada.",
    ErrorCode.AUTOMATION_INVALID_CONFIG: "Configuração da automação é inválida.",
    ErrorCode.AUTOMATION_EXECUTION_FAILED: "Falha ao executar a automação.",
    ErrorCode.LLM_TIMEOUT: "O modelo de IA demorou demais para responder.",
    ErrorCode.LLM_RATE_LIMIT: "Muitas requisições para o modelo de IA. Tente novamente.",
    ErrorCode.LLM_PROVIDER_ERROR: "O provedor de IA retornou um erro.",
    ErrorCode.LLM_TOKEN_LIMIT_EXCEEDED: "Conteúdo excede o limite suportado pelo modelo.",
    ErrorCode.LLM_INVALID_RESPONSE: "Resposta do modelo de IA em formato inválido.",
    ErrorCode.RAG_INGEST_FAILED: "Falha ao ingerir conteúdo no mecanismo de busca semântica.",
    ErrorCode.RAG_QUERY_FAILED: "Falha ao consultar o mecanismo de busca semântica.",
    ErrorCode.RAG_EMBEDDER_FAILED: "Falha ao gerar embeddings do conteúdo.",
    ErrorCode.SQS_PUBLISH_FAILED: "Falha ao enviar mensagem para a fila.",
    ErrorCode.SQS_CONSUME_FAILED: "Falha ao consumir mensagem da fila.",
    ErrorCode.SQS_DLQ_MESSAGE: "Mensagem enviada para a fila de erros.",
    ErrorCode.HARDWARE_DETECTION_ERROR: "Falha ao detectar hardware disponível.",
    ErrorCode.GPU_INITIALIZATION_ERROR: "Falha ao inicializar a GPU.",
    ErrorCode.CUDA_COMPATIBILITY_ERROR: "Versão de CUDA incompatível.",
    ErrorCode.CUDA_OUT_OF_MEMORY: "Memória da GPU insuficiente.",
    ErrorCode.MODEL_LOAD_ERROR: "Falha ao carregar o modelo.",
    ErrorCode.BILLING_INSUFFICIENT_CREDITS: "Créditos insuficientes para realizar essa operação.",
    ErrorCode.BILLING_PAYMENT_FAILED: "Falha ao processar o pagamento.",
    ErrorCode.BILLING_SUBSCRIPTION_NOT_FOUND: "Assinatura não encontrada.",
    ErrorCode.BILLING_PENDING_SUBSCRIPTION_EXISTS: "Já existe uma assinatura pendente.",
    ErrorCode.BILLING_PLAN_NOT_FOUND: "Plano não encontrado.",
    ErrorCode.INTEGRATION_NOT_FOUND: "Integração não encontrada.",
    ErrorCode.INTEGRATION_INVALID_CONFIG: "Configuração da integração é inválida.",
    ErrorCode.PROJECT_NOT_FOUND: "Projeto não encontrado.",
    ErrorCode.SPRINT_NOT_FOUND: "Sprint não encontrada.",
    ErrorCode.SPRINT_ITEM_INVALID_POLYMORPHISM: "Item da sprint inválido.",
    ErrorCode.SPRINT_ITEM_DUPLICATE: "Esse item já está na sprint.",
    ErrorCode.SPRINT_INVALID_STATUS: "Operação não permitida para o status atual da sprint.",
    ErrorCode.ROADMAP_NOT_FOUND: "Roadmap não encontrado.",
    ErrorCode.ENTITY_LINK_NOT_FOUND: "Vínculo não encontrado.",
    ErrorCode.ENTITY_LINK_INVALID_TYPES: "Tipos de origem/destino ou tipo de vínculo inválidos.",
    ErrorCode.ENTITY_LINK_ALREADY_EXISTS: "Esse vínculo já existe.",
    ErrorCode.ENTITY_LINK_ACCESS_DENIED: "Você não tem acesso a esse vínculo.",
    ErrorCode.TEAM_NOT_FOUND: "Time não encontrado.",
    ErrorCode.TEAM_ACCESS_DENIED: "Você não tem acesso a esse time.",
    ErrorCode.VALIDATION_ERROR: "Os dados enviados são inválidos.",
    ErrorCode.BAD_REQUEST: "Requisição inválida.",
    ErrorCode.NOT_FOUND: "Recurso não encontrado.",
    ErrorCode.CONFLICT: "Conflito de dados.",
    ErrorCode.INTERNAL_ERROR: "Erro interno. Tente novamente em instantes.",
    ErrorCode.SERVICE_UNAVAILABLE: "Serviço temporariamente indisponível.",
}


DEFAULT_RECOVERY_BY_CODE: dict[ErrorCode, RecoveryAction] = {
    ErrorCode.AUTH_TOKEN_EXPIRED: RecoveryAction.REFRESH_TOKEN,
    ErrorCode.LLM_TIMEOUT: RecoveryAction.RETRY_WITH_BACKOFF,
    ErrorCode.LLM_RATE_LIMIT: RecoveryAction.RETRY_WITH_BACKOFF,
    ErrorCode.LLM_PROVIDER_ERROR: RecoveryAction.FALLBACK_MODEL,
    ErrorCode.LLM_TOKEN_LIMIT_EXCEEDED: RecoveryAction.FALLBACK_MODEL,
    ErrorCode.CUDA_OUT_OF_MEMORY: RecoveryAction.FALLBACK_CPU,
    ErrorCode.SQS_CONSUME_FAILED: RecoveryAction.RETRY_WITH_BACKOFF,
    ErrorCode.SQS_PUBLISH_FAILED: RecoveryAction.RETRY_WITH_BACKOFF,
    ErrorCode.RAG_QUERY_FAILED: RecoveryAction.RETRY,
    ErrorCode.RAG_INGEST_FAILED: RecoveryAction.RETRY,
}


def status_for(code: ErrorCode) -> int:
    return DEFAULT_STATUS_BY_CODE.get(code, 500)


def default_message_for(code: ErrorCode) -> str:
    return DEFAULT_MESSAGE_BY_CODE.get(code, "Ocorreu um erro.")


def recovery_action_for(code: ErrorCode) -> RecoveryAction:
    return DEFAULT_RECOVERY_BY_CODE.get(code, RecoveryAction.NONE)


__all__ = [
    "DEFAULT_MESSAGE_BY_CODE",
    "DEFAULT_RECOVERY_BY_CODE",
    "DEFAULT_STATUS_BY_CODE",
    "ErrorCode",
    "RecoveryAction",
    "default_message_for",
    "recovery_action_for",
    "status_for",
]

# innovanote-observability

Lib compartilhada de observabilidade para os microserviços InnovaNote.

Padroniza logging estruturado em JSON, propagação de `correlation_id`, error codes, tracing AWS X-Ray e métricas CloudWatch EMF — tudo dentro do free tier AWS.

## Instalação

```bash
# Recomendado (instala via SSH a partir da tag do repo privado)
pip install "innovanote-observability @ git+ssh://git@github.com/sempejunior/innovanote-observability-.git@v0.1.0"

# Em requirements.txt:
# innovanote-observability @ git+ssh://git@github.com/sempejunior/innovanote-observability-.git@v0.1.0

# Alternativa: baixar wheel anexado ao GitHub Release
# gh release download v0.1.0 --repo sempejunior/innovanote-observability- --pattern "*.whl"
# pip install innovanote_observability-0.1.0-py3-none-any.whl
```

> **Por que não GitHub Packages?** GitHub Packages **não hospeda registry PyPI** (suporta Maven/npm/NuGet/Docker). O fluxo oficial recomendado para libs Python privadas no GitHub é via tag do repo + wheel anexado à Release. Sem custo, sem PAT extra além do acesso SSH ao repo.

Extras opcionais:

```bash
pip install "innovanote-observability[fastapi]"  # middleware + exception handlers + instrument(app)
pip install "innovanote-observability[aws]"      # boto3 helpers (SQS)
pip install "innovanote-observability[xray]"     # AWS X-Ray tracing
pip install "innovanote-observability[all]"      # tudo acima
```

---

## Uso recomendado (API alta — "import + decorator")

### 1. FastAPI — uma linha instrumenta tudo

```python
from fastapi import FastAPI
from innovanote_observability import instrument

app = FastAPI()
instrument(app, service_name="front-api")
# Pronto. Já tem:
#  - logging JSON estruturado
#  - correlation_id propagando (header X-Correlation-ID)
#  - X-Ray tracing (se XRAY_ENABLED=true)
#  - exception handlers padronizados (AppException, HTTPException, ValidationError, Exception)
#  - rotas GET /health e GET /ready
```

### 2. Decorator universal `@observed` em qualquer método

```python
from innovanote_observability import observed

@observed
async def create_note(user_id: str, content: str) -> Note:
    ...
# Loga start/end/duration/exceções, abre subsegmento X-Ray,
# herda correlation_id do contexto da request automaticamente.

@observed(operation="ingest_chunk", include_args=True)
def process_chunk(chunk_id: str): ...
```

### 3. Worker SQS — `@sqs_message_handler` per-message

```python
from innovanote_observability import sqs_message_handler

@sqs_message_handler
def process(message: dict) -> None:
    # logs e métricas daqui já vêm com correlation_id da mensagem
    ...
```

Combine com seu loop de polling existente:

```python
for msg in sqs_client.receive_message(...)["Messages"]:
    process(msg)  # decorator cuida de contexto/X-Ray/erros
```

### 4. Publicar em SQS com correlation_id automático

```python
from innovanote_observability import sqs

sqs.publish(queue_url, {"recording_id": "rec_42"})
# correlation_id atual do LogContext é injetado em MessageAttributes
```

### 5. Logs estruturados com auto-config

```python
from innovanote_observability import get_logger, LogEvent

logger = get_logger(__name__)  # auto-configura na primeira chamada (lê env vars)

logger.info(
    "Recording uploaded",
    extra={"event": LogEvent.RECORDING_UPLOADED, "recording_id": "rec_42"},
)
```

Env vars suportadas:

| Variável | Default | Propósito |
|---|---|---|
| `NAME_MICROSERVICE` / `SERVICE_NAME` | `unknown-service` | Nome do serviço no log |
| `ENVIRONMENT` / `APP_ENV` | `unknown` | dev/staging/prod |
| `SERVICE_VERSION` | `0.0.0` | Versão para correlação com deploys |
| `LOG_LEVEL` | `INFO` | DEBUG/INFO/WARNING/ERROR |
| `XRAY_ENABLED` | `false` | Liga AWS X-Ray |
| `XRAY_DAEMON_ADDRESS` | `127.0.0.1:2000` | Endereço do daemon X-Ray |
| `EMF_NAMESPACE` | `InnovaNote` | Namespace das métricas CloudWatch EMF |

---

## API low-level (escape hatch)

Para casos avançados, todos os primitivos continuam acessíveis:

```python
from innovanote_observability import (
    configure_logging,          # config explícita
    LogContext,                 # context manager de contextvars
    log_operation,              # decorator low-level (sem X-Ray)
    log_performance,
    log_errors,
)
from innovanote_observability.middleware_fastapi import (
    CorrelationMiddleware,
    register_exception_handlers,
)
from innovanote_observability.sqs_helpers import publish, sqs_message_context
from innovanote_observability.tracing import xray_trace, xray_subsegment
from innovanote_observability.metrics import emit_metric, emit_llm_metrics
```

---

## Métricas CloudWatch (EMF, free tier)

```python
from innovanote_observability import emit_llm_metrics

emit_llm_metrics(
    model="gpt-4o-mini",
    provider="openai",
    tokens_input=1200,
    tokens_output=350,
    cost_usd=0.0021,
    latency_ms=820.5,
    user_id="user_123",
)
# Vira log JSON com envelope _aws.CloudWatchMetrics; CloudWatch
# converte automaticamente em métricas (sem chamar PutMetricData).
```

---

## Documentação

- Plano completo: `documents/demandas/DEMANDA_padronizacao_observabilidade.md` (no repo audio local).
- Contrato de log: `docs/LOG_CONTRACT.md` (a ser escrito na Fase 5).
- Runbook de queries CloudWatch Logs Insights: `docs/OBSERVABILITY_RUNBOOK.md` (a ser escrito na Fase 5).

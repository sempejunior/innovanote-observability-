from __future__ import annotations

import logging
from io import StringIO

import pytest

from innovanote_observability import logging_config
from innovanote_observability.logging_config import JsonLogFormatter
from innovanote_observability.logging_context import clear_context
from innovanote_observability.logging_filters import (
    RequestContextFilter,
    SensitiveDataFilter,
)


@pytest.fixture(autouse=True)
def _reset_context():
    clear_context()
    yield
    clear_context()


@pytest.fixture
def capture_json_logs():
    """Captura logs emitidos pelo root logger como linhas JSON em memória.

    Marca a lib como já configurada para que ``ensure_configured`` lazy não
    re-aplique o dictConfig (que sobrescreveria nosso handler).
    """
    buffer = StringIO()
    handler = logging.StreamHandler(buffer)
    handler.setFormatter(JsonLogFormatter())
    handler.addFilter(SensitiveDataFilter())
    handler.addFilter(
        RequestContextFilter(
            service_name="test-service",
            environment="test",
            service_version="0.0.1",
        )
    )
    root = logging.getLogger()
    original_handlers = root.handlers[:]
    original_level = root.level
    original_configured = logging_config._configured
    root.handlers = [handler]
    root.setLevel(logging.DEBUG)
    logging_config._configured = True
    try:
        yield buffer
    finally:
        root.handlers = original_handlers
        root.setLevel(original_level)
        logging_config._configured = original_configured

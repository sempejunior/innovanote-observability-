from __future__ import annotations

import pytest

pytest.importorskip("fastapi")

from fastapi import FastAPI, HTTPException  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from pydantic import BaseModel  # noqa: E402

from innovanote_observability.error_codes import ErrorCode  # noqa: E402
from innovanote_observability.exceptions import (  # noqa: E402
    InsufficientCreditsError,
    NotFoundException,
)
from innovanote_observability.middleware_fastapi import (  # noqa: E402
    CorrelationMiddleware,
    register_exception_handlers,
)


class _Body(BaseModel):
    name: str
    age: int


def _make_app() -> FastAPI:
    app = FastAPI()
    app.add_middleware(CorrelationMiddleware)
    register_exception_handlers(app)

    @app.get("/ok")
    def ok():
        return {"ok": True}

    @app.get("/missing")
    def missing():
        raise NotFoundException(error_code=ErrorCode.NOTE_NOT_FOUND)

    @app.get("/credits")
    def credits():
        raise InsufficientCreditsError(credits_remaining=1, credits_required=10)

    @app.get("/boom")
    def boom():
        raise RuntimeError("kaboom")

    @app.get("/legacy")
    def legacy():
        raise HTTPException(status_code=403, detail="not allowed")

    @app.get("/legacy-dict")
    def legacy_dict():
        raise HTTPException(status_code=409, detail={"code": "CUSTOM_CONFLICT", "message": "dup", "field": "x"})

    @app.post("/validate")
    def validate(payload: _Body):
        return payload

    return app


class TestCorrelationMiddleware:
    def test_generates_correlation_id_when_absent(self):
        client = TestClient(_make_app())
        r = client.get("/ok")
        assert r.status_code == 200
        assert r.headers.get("X-Correlation-ID")

    def test_propagates_existing_correlation_id(self):
        client = TestClient(_make_app())
        r = client.get("/ok", headers={"X-Correlation-ID": "test-cid-42"})
        assert r.headers["X-Correlation-ID"] == "test-cid-42"


class TestExceptionHandlers:
    def test_app_exception_returns_standard_body(self):
        client = TestClient(_make_app())
        r = client.get("/missing")
        assert r.status_code == 404
        body = r.json()
        assert body["error"]["code"] == "NOTE_NOT_FOUND"
        assert body["error"]["status"] == 404
        assert "Nota" in body["error"]["message"]
        assert body["error"]["correlation_id"]

    def test_insufficient_credits_details(self):
        client = TestClient(_make_app())
        r = client.get("/credits")
        assert r.status_code == 402
        body = r.json()
        assert body["error"]["details"] == {"credits_remaining": 1, "credits_required": 10}

    def test_unhandled_exception_returns_500(self):
        client = TestClient(_make_app(), raise_server_exceptions=False)
        r = client.get("/boom")
        assert r.status_code == 500
        assert r.json()["error"]["code"] == "INTERNAL_ERROR"

    def test_legacy_http_exception_with_string_detail(self):
        client = TestClient(_make_app())
        r = client.get("/legacy")
        assert r.status_code == 403
        body = r.json()
        assert body["error"]["status"] == 403
        assert body["error"]["message"] == "not allowed"

    def test_legacy_http_exception_with_dict_detail(self):
        client = TestClient(_make_app())
        r = client.get("/legacy-dict")
        assert r.status_code == 409
        body = r.json()
        assert body["error"]["code"] == "CUSTOM_CONFLICT"
        assert body["error"]["details"] == {"field": "x"}

    def test_validation_error_returns_422_with_fields(self):
        client = TestClient(_make_app())
        r = client.post("/validate", json={"name": "x"})
        assert r.status_code == 422
        body = r.json()
        assert body["error"]["code"] == "VALIDATION_ERROR"
        assert "fields" in body["error"]["details"]
        fields = body["error"]["details"]["fields"]
        assert any("age" in str(f.get("loc", [])) for f in fields)

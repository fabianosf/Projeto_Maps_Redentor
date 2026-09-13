# ----------------------------
# Deus seja Louvado!
# ----------------------------
"""Testes Fase 2 — correlation ID, headers, guards de ambiente."""

from __future__ import annotations

import pytest

from BackEnd.app import _assert_runtime_guards
from BackEnd.auth_session import cookie_samesite


def test_correlation_id_header_na_resposta(client):
    resp = client.get(
        "/api/v1/auth/me",
        headers={"X-Request-ID": "fase2-corr-abc123"},
    )
    assert resp.status_code == 200
    assert resp.headers.get("X-Request-ID") == "fase2-corr-abc123"


def test_correlation_id_gerado_sem_header(client):
    resp = client.get("/api/v1/auth/me")
    assert resp.status_code == 200
    cid = resp.headers.get("X-Request-ID")
    assert cid
    assert len(cid) >= 8


def test_json_error_inclui_correlation_id(client):
    resp = client.get("/api/v1/mapas")
    assert resp.status_code == 401
    body = resp.get_json()
    assert body["ok"] is False
    assert body.get("correlation_id")
    assert resp.headers.get("X-Request-ID")


def test_hsts_quando_cookie_secure(monkeypatch, client):
    monkeypatch.setenv("REDMAPA_COOKIE_SECURE", "true")
    # Reaplica after_request já registrado — header setdefault no request
    # depende do env no momento do after_request.
    resp = client.get("/api/v1/auth/me")
    assert resp.headers.get("Strict-Transport-Security", "").startswith("max-age=")


def test_cookie_samesite_none_exige_secure(monkeypatch):
    monkeypatch.setenv("REDMAPA_COOKIE_SECURE", "false")
    monkeypatch.setenv("REDMAPA_COOKIE_SAMESITE", "none")
    assert cookie_samesite() == "lax"
    monkeypatch.setenv("REDMAPA_COOKIE_SECURE", "true")
    assert cookie_samesite() == "None"


def test_production_rejeita_erp_mock(monkeypatch):
    monkeypatch.setenv("REDMAPA_ENV", "production")
    monkeypatch.setenv("ERP_PROVIDER", "mock")
    monkeypatch.setenv("FLASK_DEBUG", "0")
    with pytest.raises(RuntimeError, match="não permite ERP_PROVIDER=mock"):
        _assert_runtime_guards()


def test_production_rejeita_flask_debug(monkeypatch):
    monkeypatch.setenv("REDMAPA_ENV", "production")
    monkeypatch.setenv("ERP_PROVIDER", "oracle")
    monkeypatch.setenv("FLASK_DEBUG", "1")
    with pytest.raises(RuntimeError, match="FLASK_DEBUG"):
        _assert_runtime_guards()

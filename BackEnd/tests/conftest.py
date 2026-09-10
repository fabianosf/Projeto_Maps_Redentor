# ----------------------------
# Deus seja Louvado!
# ----------------------------
"""Fixtures pytest — app Flask + SQLite isolado."""

from __future__ import annotations

import pytest

from BackEnd.login_attempt_store import _lock as _tentativas_lock
from BackEnd.login_attempt_store import _tentativas_falhas
from BackEnd.session_store import password_change_token_store, session_store
from BackEnd.tests.sqlite_dal import SqliteTestDal, build_test_app

SENHA_VALIDA = "Senha@123"
SENHA_ERRADA = "Errada@99"


@pytest.fixture(autouse=True)
def _limpar_stores_em_memoria():
    with _tentativas_lock:
        _tentativas_falhas.clear()
    session_store._sessions.clear()
    password_change_token_store._tokens.clear()
    yield
    with _tentativas_lock:
        _tentativas_falhas.clear()
    session_store._sessions.clear()
    password_change_token_store._tokens.clear()


@pytest.fixture
def dal():
    return SqliteTestDal()


@pytest.fixture
def app(dal, monkeypatch):
    # Dev local / testes: provider mock explícito.
    monkeypatch.setenv("ERP_PROVIDER", "mock")
    monkeypatch.setenv("ERP_ALLOW_MANUAL_USER_CREATE", "1")
    monkeypatch.setenv("REDMAPA_ERP_ENABLED", "0")
    application = build_test_app(dal)
    return application


@pytest.fixture
def client(app):
    return app.test_client()


def login(client, matricula: str, senha: str = SENHA_VALIDA):
    return client.post(
        "/api/v1/auth/login",
        json={"matricula": matricula, "senha": senha},
    )


def auth_client(client, matricula: str, senha: str = SENHA_VALIDA):
    """Faz login e devolve o mesmo client com cookie de sessão."""
    resp = login(client, matricula, senha)
    assert resp.status_code == 200, resp.get_json()
    body = resp.get_json()
    assert body.get("ok") is True
    assert body.get("trocar_senha") is False
    return client

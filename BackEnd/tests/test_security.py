# ----------------------------
# Deus seja Louvado!
# ----------------------------
"""Testes de segurança — cookies, headers, CORS, login_attempt, senha."""

from __future__ import annotations

import bcrypt

from BackEnd.auth_service import hash_senha, verificar_senha
from BackEnd.auth_session import build_session_cookie, cookie_secure
from BackEnd.constants import gerar_senha_provisoria
from BackEnd.login_attempt_store import (
    obter_tentativas,
    registrar_tentativa_falha,
    resetar_tentativas,
)
from BackEnd.security import _cors_origins
from BackEnd.tests.conftest import SENHA_VALIDA, login


def test_login_continua_funcionando(client):
    resp = login(client, "1", SENHA_VALIDA)
    assert resp.status_code == 200
    assert resp.get_json()["ok"] is True
    assert resp.get_json()["usuario"]["matricula"] == "1"


def test_cookie_sessao_httponly_samesite(client):
    resp = login(client, "1", SENHA_VALIDA)
    assert resp.status_code == 200
    set_cookie = resp.headers.get("Set-Cookie", "")
    assert "redmapa_sid=" in set_cookie
    assert "HttpOnly" in set_cookie
    assert "SameSite=Lax" in set_cookie or "SameSite=lax" in set_cookie.lower()


def test_cookie_secure_segue_env(monkeypatch):
    monkeypatch.setenv("REDMAPA_COOKIE_SECURE", "true")
    assert cookie_secure() is True
    cookie = build_session_cookie("abc")
    assert cookie["httponly"] is True
    assert cookie["secure"] is True
    assert cookie["samesite"] == "lax"

    monkeypatch.setenv("REDMAPA_COOKIE_SECURE", "false")
    assert cookie_secure() is False
    cookie2 = build_session_cookie("xyz")
    assert cookie2["secure"] is False


def test_security_headers_presentes(client):
    resp = client.get("/api/v1/auth/me")  # sem sessão: 200 autenticado=false; headers aplicam
    assert resp.status_code == 200
    assert resp.headers.get("X-Content-Type-Options") == "nosniff"
    assert resp.headers.get("X-Frame-Options") == "DENY"
    csp = resp.headers.get("Content-Security-Policy", "")
    assert "default-src 'none'" in csp
    assert "frame-ancestors 'none'" in csp


def test_cors_nunca_wildcard(monkeypatch):
    monkeypatch.setenv(
        "REDMAPA_CORS_ORIGINS",
        "http://localhost:5173,*,https://app.exemplo.com",
    )
    origins = list(_cors_origins())
    assert "*" not in origins
    assert "http://localhost:5173" in origins
    assert "https://app.exemplo.com" in origins


def test_senha_provisoria_aleatoria_obedece_politica():
    samples = {gerar_senha_provisoria() for _ in range(20)}
    assert len(samples) >= 15
    assert "12345" not in samples
    for s in samples:
        assert len(s) >= 8
        assert any(c.isupper() for c in s)
        assert any(c.islower() for c in s)
        assert any(c.isdigit() for c in s)
        assert any(c in '!@#$%^&*(),.?":{}|<>_-+=[]\\;/`~' for c in s)


def test_hash_bcrypt_roundtrip():
    plana = gerar_senha_provisoria()
    hashed = hash_senha(plana)
    assert hashed.startswith("$2")
    assert verificar_senha(plana, hashed) is True
    assert verificar_senha("outra", hashed) is False
    # Confirma uso de bcrypt
    assert bcrypt.checkpw(plana.encode(), hashed.encode())


def test_login_attempt_store_incrementa_e_reseta():
    resetar_tentativas("888")
    assert obter_tentativas("888") == 0
    assert registrar_tentativa_falha("888") == 1
    assert registrar_tentativa_falha("888") == 2
    assert obter_tentativas("888") == 2
    resetar_tentativas("888")
    assert obter_tentativas("888") == 0

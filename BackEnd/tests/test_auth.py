# ----------------------------
# Deus seja Louvado!
# ----------------------------
"""Testes de autenticação — login, bloqueio, logout, primeiro acesso."""

from __future__ import annotations

from BackEnd.tests.conftest import SENHA_ERRADA, SENHA_VALIDA, auth_client, login


def test_login_valido(client):
    resp = login(client, "1", SENHA_VALIDA)
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["ok"] is True
    assert data["trocar_senha"] is False
    assert data["usuario"]["matricula"] == "1"
    assert data["usuario"]["codigo_perfil"] == 1
    assert "redmapa_sid" in resp.headers.get("Set-Cookie", "")


def test_login_invalido_senha(client):
    resp = login(client, "1", SENHA_ERRADA)
    assert resp.status_code == 401
    data = resp.get_json()
    assert data["ok"] is False
    assert data["codigo"] == "senha_invalida"


def test_login_matricula_inexistente(client):
    resp = login(client, "77777", SENHA_VALIDA)
    assert resp.status_code == 401
    assert resp.get_json()["codigo"] == "usuario_invalido"


def test_bloqueio_apos_n_tentativas(client, dal):
    for _ in range(2):
        r = login(client, "1", SENHA_ERRADA)
        assert r.status_code == 401
        assert r.get_json()["codigo"] == "senha_invalida"

    r3 = login(client, "1", SENHA_ERRADA)
    assert r3.status_code == 401
    data = r3.get_json()
    assert data["codigo"] == "limite_tentativas"
    assert "Limite" in data["mensagem"]

    # Usuário inativado no banco
    row = dal.read("SELECT ativo FROM tb_usuario WHERE matricula = ?", ("1",))
    assert int(row.iloc[0]["ativo"]) == 0

    # Mesmo senha correta falha (inativo)
    r4 = login(client, "1", SENHA_VALIDA)
    assert r4.status_code == 401
    assert r4.get_json()["codigo"] == "usuario_invalido"


def test_logout(client):
    auth_client(client, "1")
    me = client.get("/api/v1/auth/me")
    assert me.status_code == 200

    out = client.post("/api/v1/auth/logout")
    assert out.status_code == 200
    assert out.get_json()["ok"] is True

    me2 = client.get("/api/v1/auth/me")
    assert me2.status_code == 401


def test_primeiro_acesso_troca_senha(client):
    resp = login(client, "99", SENHA_VALIDA)
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["ok"] is True
    assert data["trocar_senha"] is True
    assert data.get("change_token")
    # Sem sessão autenticada
    cookie = resp.headers.get("Set-Cookie", "")
    assert "redmapa_sid=;" in cookie.replace(" ", "") or "redmapa_sid=''" in cookie or (
        "Max-Age=0" in cookie
    )

    token = data["change_token"]
    nova = "NovaSenha@1"
    trocar = client.post(
        "/api/v1/auth/change-password",
        json={
            "change_token": token,
            "nova_senha": nova,
            "confirmacao_senha": nova,
        },
    )
    assert trocar.status_code == 200
    assert trocar.get_json()["ok"] is True

    # Login com senha antiga falha; nova funciona e sem trocar_senha
    assert login(client, "99", SENHA_VALIDA).status_code == 401
    ok = login(client, "99", nova)
    assert ok.status_code == 200
    assert ok.get_json()["trocar_senha"] is False

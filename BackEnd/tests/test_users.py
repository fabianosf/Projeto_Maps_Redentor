# ----------------------------
# Deus seja Louvado!
# ----------------------------
"""Testes de usuários — CRUD, senha provisória, reset Admin-only."""

from __future__ import annotations

from BackEnd.tests.conftest import SENHA_VALIDA, auth_client, login


def test_criar_usuario_senha_nao_fix(client):
    auth_client(client, "1")
    resp = client.post(
        "/api/v1/users",
        json={
            "matricula": "55",
            "nome": "Usuario Novo",
            "codigo_perfil": 3,
        },
    )
    assert resp.status_code == 201
    data = resp.get_json()
    assert data["ok"] is True
    usuario = data["usuario"]
    senha_tmp = usuario.get("senha_temporaria")
    assert senha_tmp
    assert senha_tmp != "12345"
    assert len(senha_tmp) >= 12
    assert usuario["trocar_senha"] in (1, True)

    # Segunda criação gera senha distinta
    resp2 = client.post(
        "/api/v1/users",
        json={
            "matricula": "56",
            "nome": "Outro Usuario",
            "codigo_perfil": 3,
        },
    )
    assert resp2.status_code == 201
    senha2 = resp2.get_json()["usuario"]["senha_temporaria"]
    assert senha2 != senha_tmp


def test_listar_usuarios(client):
    auth_client(client, "1")
    resp = client.get("/api/v1/users")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["ok"] is True
    mats = {u["matricula"] for u in data["usuarios"]}
    assert "1" in mats
    assert "3" in mats


def test_inativacao_logica(client):
    auth_client(client, "1")
    # Cria alvo
    criado = client.post(
        "/api/v1/users",
        json={"matricula": "44", "nome": "Para Inativar", "codigo_perfil": 3},
    )
    assert criado.status_code == 201
    id_u = criado.get_json()["usuario"]["id_usuario"]

    excl = client.delete(f"/api/v1/users/{id_u}")
    assert excl.status_code == 200
    assert excl.get_json()["ok"] is True

    # Soft delete: ainda listável ou não — serviço lista todos; ativo=0
    lista = client.get("/api/v1/users").get_json()["usuarios"]
    alvo = next(u for u in lista if u["id_usuario"] == id_u)
    assert int(alvo["ativo"]) == 0

    # Segunda exclusão → já inativo
    excl2 = client.delete(f"/api/v1/users/{id_u}")
    assert excl2.status_code == 409


def test_reset_bloqueado_para_inspetor(client):
    # Admin cria usuário alvo
    auth_client(client, "1")
    criado = client.post(
        "/api/v1/users",
        json={"matricula": "66", "nome": "Alvo Reset", "codigo_perfil": 2,
              "id_empresa": 1, "id_turno": 1, "id_local": 1},
    )
    assert criado.status_code == 201
    id_u = criado.get_json()["usuario"]["id_usuario"]

    # Logout admin / login inspetor
    client.post("/api/v1/auth/logout")
    auth_client(client, "3")

    # Inspetor acessa listagem (config) mas reset é Admin-only
    lista = client.get("/api/v1/users")
    assert lista.status_code == 200

    reset = client.post(f"/api/v1/users/{id_u}/reset-password")
    assert reset.status_code == 403
    assert reset.get_json()["codigo"] == "perfil_negado"


def test_reset_admin_ok(client):
    auth_client(client, "1")
    criado = client.post(
        "/api/v1/users",
        json={"matricula": "67", "nome": "Reset Admin", "codigo_perfil": 3},
    )
    id_u = criado.get_json()["usuario"]["id_usuario"]
    reset = client.post(f"/api/v1/users/{id_u}/reset-password")
    assert reset.status_code == 200
    body = reset.get_json()
    assert body["ok"] is True
    assert body["usuario"]["senha_temporaria"]
    assert body["usuario"]["senha_temporaria"] != "12345"

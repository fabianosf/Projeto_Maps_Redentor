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

    # POST com mesma matrícula reativa (mesmo id)
    reat = client.post(
        "/api/v1/users",
        json={"matricula": "44", "nome": "Reativado Ok", "codigo_perfil": 3},
    )
    assert reat.status_code == 200
    body = reat.get_json()
    assert body["ok"] is True
    assert body["reativado"] is True
    assert body["senha_temporaria"]
    assert body["usuario"]["id_usuario"] == id_u
    assert body["usuario"]["nome"] == "Reativado Ok"
    assert int(body["usuario"]["ativo"]) in (1, True) or body["usuario"]["ativo"] is True

    # Ativo: duplicata
    dup = client.post(
        "/api/v1/users",
        json={"matricula": "44", "nome": "Dup", "codigo_perfil": 3},
    )
    assert dup.status_code == 409
    assert dup.get_json()["codigo"] == "matricula_duplicada"


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


def test_erp_mock_get_e_post_sem_oracle(client):
    """Provider mock local explícito: GET usa mock; POST não toca Oracle."""
    auth_client(client, "1")
    erp = client.get("/api/v1/users/erp-funcionario/59800")
    assert erp.status_code == 200
    func = erp.get_json()
    assert func["matricula"] == "59800"
    assert func["nome"] == "Jose Ricardo"
    assert func["origem"] == "mock"
    assert func["foto_url"] is None
    assert func["ativo"] is True

    miss = client.get("/api/v1/users/erp-funcionario/11111")
    assert miss.status_code == 404
    assert miss.get_json()["codigo"] == "funcionario_nao_encontrado"

    criado = client.post(
        "/api/v1/users",
        json={
            "matricula": "59800",
            "nome": "Jose Ricardo",
            "codigo_perfil": 3,
        },
    )
    assert criado.status_code == 201
    assert criado.get_json()["usuario"]["matricula"] == "59800"


def test_erp_funcionario_normaliza_espacos(client):
    auth_client(client, "1")
    erp = client.get("/api/v1/users/erp-funcionario/ 59 800 ")
    assert erp.status_code == 200
    body = erp.get_json()
    assert body["matricula"] == "59800"
    assert body["nome"] == "Jose Ricardo"


def test_erp_funcionario_mock_seed_59800(client):
    auth_client(client, "1")
    resp = client.get("/api/v1/users/erp-funcionario/59800")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["matricula"] == "59800"
    assert body["nome"] == "Jose Ricardo"
    assert body["origem"] == "mock"


def test_erp_funcionario_mock_nao_inclui_admins_reais(client):
    """59492/59817 não devem existir na lista fixa mock (produção usa Oracle)."""
    auth_client(client, "1")
    for mat in ("59492", "59817"):
        resp = client.get(f"/api/v1/users/erp-funcionario/{mat}")
        assert resp.status_code == 404
        assert resp.get_json()["codigo"] == "funcionario_nao_encontrado"


def test_erp_funcionario_mock_inexistente_404(client):
    auth_client(client, "1")
    resp = client.get("/api/v1/users/erp-funcionario/11111")
    assert resp.status_code == 404
    body = resp.get_json()
    assert body["codigo"] == "funcionario_nao_encontrado"
    assert "não encontrada" in body["mensagem"].lower()


def test_erp_funcionario_oracle_indisponivel_503(client, monkeypatch):
    from BackEnd.erp_funcionario_service import ErpError

    auth_client(client, "1")
    monkeypatch.setenv("ERP_PROVIDER", "oracle")
    monkeypatch.setattr(
        "BackEnd.users_routes.build_erp_funcionario_service",
        lambda: ErpError(
            "Não foi possível consultar o cadastro corporativo no momento. Tente novamente.",
            "erp_indisponivel",
        ),
    )
    resp = client.get("/api/v1/users/erp-funcionario/59800")
    assert resp.status_code == 503
    body = resp.get_json()
    assert body["codigo"] == "erp_indisponivel"


def test_by_matricula_consulta_erp_primeiro_prefill(client):
    """Matrícula no mock ERP e ausente em tb_usuario → prefill (não 404 local)."""
    auth_client(client, "1")
    resp = client.get("/api/v1/users/by-matricula/59800")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["ok"] is True
    assert body["ja_cadastrado"] is False
    assert body["usuario"]["matricula"] == "59800"
    assert body["usuario"]["nome"] == "Jose Ricardo"
    assert body["usuario"].get("id_usuario") in (None, 0) or "id_usuario" not in body["usuario"]
    assert "rh" in body.get("mensagem", "").lower() or "cadastro" in body.get("mensagem", "").lower()


def test_by_matricula_ja_cadastrado(client):
    auth_client(client, "1")
    criado = client.post(
        "/api/v1/users",
        json={"matricula": "59800", "nome": "Jose Ricardo", "codigo_perfil": 3},
    )
    assert criado.status_code == 201
    id_u = criado.get_json()["usuario"]["id_usuario"]

    resp = client.get("/api/v1/users/by-matricula/59800")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["ja_cadastrado"] is True
    assert body["usuario"]["id_usuario"] == id_u
    assert body["usuario"]["matricula"] == "59800"


def test_by_matricula_nao_encontrada_rh_404(client):
    auth_client(client, "1")
    resp = client.get("/api/v1/users/by-matricula/11111")
    assert resp.status_code == 404
    body = resp.get_json()
    assert body["codigo"] == "nao_encontrado_rh"
    assert "rh" in body["mensagem"].lower()


def test_by_matricula_oracle_qualquer_matricula_nao_limitada_a_seed(client, monkeypatch):
    """Com provider oracle, qualquer matrícula real do RH preenche — não só seeds mock."""
    from BackEnd.erp_funcionario_service import (
        ERPFuncionario,
        ERPFuncionarioService,
        ErpError,
    )

    class _RepoOracleReal:
        origem = "oracle"

        def consultar(self, matricula: str):
            mat = str(matricula).strip()
            if mat == "59548":
                return ERPFuncionario(
                    matricula="59548",
                    nome="Funcionario Oracle Real",
                    foto_url=None,
                    ativo=True,
                    origem="oracle",
                )
            return ErpError(
                "Matrícula não encontrada no cadastro de funcionários.",
                "funcionario_nao_encontrado",
            )

    auth_client(client, "1")
    monkeypatch.setenv("ERP_PROVIDER", "oracle")
    monkeypatch.setattr(
        "BackEnd.users_routes.build_erp_funcionario_service",
        lambda: ERPFuncionarioService(_RepoOracleReal()),
    )

    resp = client.get("/api/v1/users/by-matricula/59548")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["ok"] is True
    assert body["ja_cadastrado"] is False
    assert body["usuario"]["matricula"] == "59548"
    assert body["usuario"]["nome"] == "Funcionario Oracle Real"
    assert body["usuario"]["origem"] == "oracle"

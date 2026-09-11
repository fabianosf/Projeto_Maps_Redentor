# ----------------------------
# Deus seja Louvado!
# ----------------------------
"""Testes DesignacaoOperacional — criar, conflito ATIVA, transferência."""

from __future__ import annotations

from BackEnd.tests.conftest import auth_client


def _payload_criar(**overrides):
    base = {
        "id_usuario": 3,
        "id_empresa": 1,
        "id_turno": 1,
        "data": "2026-09-08",
        "inicio": "2026-09-08 08:00:00",
        "id_linha": None,
        "id_veiculo": None,
    }
    base.update(overrides)
    return base


def test_criar_ativa_sem_linha_veiculo(client):
    auth_client(client, "1")
    resp = client.post("/api/v1/designacoes", json=_payload_criar())
    assert resp.status_code == 201, resp.get_json()
    d = resp.get_json()["designacao"]
    assert d["status"] == "ATIVA"
    assert d["id_linha"] is None
    assert d["id_veiculo"] is None
    assert d["id_empresa"] == 1


def test_criar_segunda_ativa_conflito(client):
    auth_client(client, "1")
    r1 = client.post("/api/v1/designacoes", json=_payload_criar())
    assert r1.status_code == 201
    r2 = client.post("/api/v1/designacoes", json=_payload_criar())
    assert r2.status_code == 409
    assert r2.get_json()["codigo"] == "conflito_ativa"


def test_transferir_encerra_e_cria(client):
    auth_client(client, "1")
    cri = client.post("/api/v1/designacoes", json=_payload_criar())
    assert cri.status_code == 201
    id_antiga = cri.get_json()["designacao"]["id_designacao"]

    tr = client.post(
        "/api/v1/designacoes/transferir",
        json=_payload_criar(
            id_empresa=2,
            data="2026-09-08",
            inicio="2026-09-08 14:00:00",
        ),
    )
    assert tr.status_code == 200, tr.get_json()
    nova = tr.get_json()["designacao"]
    assert nova["status"] == "ATIVA"
    assert nova["id_empresa"] == 2
    assert nova["id_designacao"] != id_antiga

    hist = client.get("/api/v1/designacoes/historico?id_usuario=3")
    assert hist.status_code == 200
    itens = hist.get_json()["designacoes"]
    assert len(itens) == 2
    por_id = {i["id_designacao"]: i for i in itens}
    assert por_id[id_antiga]["status"] == "ENCERRADA"
    assert por_id[id_antiga]["fim"] is not None
    assert por_id[nova["id_designacao"]]["status"] == "ATIVA"


def test_apenas_uma_ativa_apos_transferir(client, dal):
    auth_client(client, "1")
    client.post("/api/v1/designacoes", json=_payload_criar())
    client.post(
        "/api/v1/designacoes/transferir",
        json=_payload_criar(id_empresa=2, inicio="2026-09-08 15:00:00"),
    )
    df = dal.read(
        "SELECT COUNT(*) AS qtd FROM tb_designacao_operacional "
        "WHERE id_usuario = 3 AND status = 'ATIVA'"
    )
    assert int(df.iloc[0]["qtd"]) == 1


def test_transferir_sem_ativa_cria_primeira(client):
    auth_client(client, "1")
    tr = client.post(
        "/api/v1/designacoes/transferir",
        json=_payload_criar(id_empresa=2, inicio="2026-09-08 09:00:00"),
    )
    assert tr.status_code == 200, tr.get_json()
    d = tr.get_json()["designacao"]
    assert d["status"] == "ATIVA"
    assert d["id_empresa"] == 2
    hist = client.get("/api/v1/designacoes/historico?id_usuario=3").get_json()
    assert len(hist["designacoes"]) == 1


def test_linha_outra_empresa_rejeitada(client):
    auth_client(client, "1")
    resp = client.post(
        "/api/v1/designacoes",
        json=_payload_criar(id_empresa=1, id_linha=3),  # linha 3 = empresa 2
    )
    assert resp.status_code == 400
    assert "empresa" in resp.get_json()["mensagem"].lower()


def test_veiculo_outra_empresa_permitido(client):
    auth_client(client, "1")
    resp = client.post(
        "/api/v1/designacoes",
        json=_payload_criar(id_empresa=1, id_veiculo=2),  # veiculo 2 = empresa 2
    )
    assert resp.status_code in (200, 201), resp.get_json()


def test_me_expoe_designacao_ativa(client):
    auth_client(client, "1")
    client.post("/api/v1/designacoes", json=_payload_criar())
    # login despachante
    client.post("/api/v1/auth/logout")
    auth_client(client, "2")
    me = client.get("/api/v1/auth/me")
    assert me.status_code == 200
    body = me.get_json()
    assert body["autenticado"] is True
    ativa = body.get("designacao_ativa")
    assert ativa is not None
    assert ativa["status"] == "ATIVA"
    assert ativa["id_usuario"] == 3


def test_transferir_somente_admin(client):
    auth_client(client, "2")  # despachante
    resp = client.post(
        "/api/v1/designacoes/transferir",
        json=_payload_criar(),
    )
    assert resp.status_code == 403

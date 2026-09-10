# ----------------------------
# Deus seja Louvado!
# ----------------------------
"""GET /api/v1/mapas/ocupacao — recursos EM_ANDAMENTO."""

from __future__ import annotations

from BackEnd.tests.conftest import auth_client


def _payload_mapa(**overrides):
    base = {
        "id_turno": 1,
        "id_empresa": 1,
        "data": "2026-09-08",
        "inicio_jornada_des": "2026-09-08 05:00:00",
        "fim_jornada_des": "2026-09-08 14:00:00",
    }
    base.update(overrides)
    return base


def _payload_item(**overrides):
    base = {
        "id_linha": 1,
        "id_veiculo": 1,
        "id_motorista": 1,
        "hor_ini_jor": "2026-09-08 08:00:00",
        "hor_fim_jor": "2026-09-08 17:00:00",
        "chegada_ponto": "2026-09-08 08:10:00",
        "inicio_real": "2026-09-08 08:10:00",
    }
    base.update(overrides)
    return base


def test_ocupacao_requer_auth(client):
    resp = client.get("/api/v1/mapas/ocupacao")
    assert resp.status_code in (401, 403)


def test_ocupacao_vazia_autenticada(client):
    auth_client(client, "1")
    resp = client.get("/api/v1/mapas/ocupacao")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body.get("ok") is True
    assert "veiculos_ocupados" in body
    assert "motoristas_ocupados" in body
    assert body["veiculos_ocupados"] == []
    assert body["motoristas_ocupados"] == []


def test_ocupacao_falha_sql_retorna_500(client, monkeypatch):
    """OperationalError / coluna ausente → HTTP 500 (nunca 200)."""
    auth_client(client, "1")

    class _FakeOpErr(Exception):
        pass

    def _boom(*_a, **_k):
        raise _FakeOpErr("Unknown column 'i.status_escala' in 'field list'")

    monkeypatch.setattr(
        "BackEnd.mapa_routes.listar_ocupacao_escalas",
        _boom,
    )
    # força classificação como falha SQL pelo nome da classe
    _FakeOpErr.__name__ = "OperationalError"

    resp = client.get("/api/v1/mapas/ocupacao")
    assert resp.status_code == 500
    body = resp.get_json()
    assert body.get("ok") is False
    assert "disponibilidade" in (body.get("message") or body.get("mensagem") or "").lower()


def test_ocupacao_listas_e_baixa(client, dal):
    auth_client(client, "1")
    dal.create(
        """
        INSERT INTO tb_veiculo (id_veiculo, codigo_veiculo, numero_frota, placa, ativo, id_empresa)
        VALUES (60, 60, 'C30000', 'OC3000', 1, 1)
        """
    )
    dal.create(
        """
        INSERT INTO tb_veiculo (id_veiculo, codigo_veiculo, numero_frota, placa, ativo, id_empresa)
        VALUES (61, 61, 'C30114', 'OC3114', 1, 1)
        """
    )
    dal.create(
        """
        INSERT INTO tb_motorista (id_motorista, matricula, nome, ativo)
        VALUES (60, '2001', 'Motorista Teste 2001', 1)
        """
    )
    dal.create(
        """
        INSERT INTO tb_motorista (id_motorista, matricula, nome, ativo)
        VALUES (61, '2002', 'Motorista Livre', 1)
        """
    )

    m = client.post("/api/v1/mapas", json=_payload_mapa())
    assert m.status_code == 201
    id_reg = m.get_json()["mapa"]["id_registro"]
    cod_map = m.get_json()["mapa"]["cod_map"]
    codigo_mapa = m.get_json()["mapa"]["codigo_mapa"]
    assert codigo_mapa == "Fut01"

    i1 = client.post(
        f"/api/v1/mapas/{id_reg}/itens",
        json=_payload_item(id_veiculo=60, id_motorista=60),
    )
    assert i1.status_code == 201, i1.get_json()
    id_item = int(i1.get_json()["item"]["id_item"])

    occ = client.get("/api/v1/mapas/ocupacao")
    assert occ.status_code == 200, occ.get_json()
    body = occ.get_json()
    assert "veiculos_ocupados" in body
    assert "motoristas_ocupados" in body
    assert any(int(v["id_veiculo"]) == 60 for v in body["veiculos_ocupados"])
    assert any(int(m["id_motorista"]) == 60 for m in body["motoristas_ocupados"])
    v0 = next(v for v in body["veiculos_ocupados"] if int(v["id_veiculo"]) == 60)
    assert v0["prefixo"] == "C30000"
    assert v0["status"] == "EM_ANDAMENTO"
    assert int(v0["id_mapa_item"]) == id_item
    assert v0.get("inicio_real") in ("08:10", "08:10:00") or str(
        v0.get("inicio_real", "")
    ).startswith("08:10")

    # Conflito veículo
    conflito_v = client.post(
        f"/api/v1/mapas/{id_reg}/itens",
        json=_payload_item(id_veiculo=60, id_motorista=61),
    )
    assert conflito_v.status_code == 409
    assert "C30000" in conflito_v.get_json()["mensagem"]
    msg_v = conflito_v.get_json()["mensagem"]
    assert codigo_mapa in msg_v or str(cod_map).zfill(5) in msg_v or str(cod_map) in msg_v

    # Conflito motorista
    conflito_m = client.post(
        f"/api/v1/mapas/{id_reg}/itens",
        json=_payload_item(id_veiculo=61, id_motorista=60),
    )
    assert conflito_m.status_code == 409
    msg_m = conflito_m.get_json()["mensagem"]
    assert "2001" in msg_m
    assert "C30000" in msg_m

    # Baixa libera
    baixa = client.post(
        f"/api/v1/mapas/itens/{id_item}/baixa",
        json={"fim_real": "2026-09-08 12:00:00"},
    )
    assert baixa.status_code == 200, baixa.get_json()

    occ2 = client.get("/api/v1/mapas/ocupacao")
    assert occ2.status_code == 200
    body2 = occ2.get_json()
    assert not any(int(v["id_veiculo"]) == 60 for v in body2["veiculos_ocupados"])
    assert not any(int(m["id_motorista"]) == 60 for m in body2["motoristas_ocupados"])

    # ENCERRADA não aparece; reuso liberado
    ok = client.post(
        f"/api/v1/mapas/{id_reg}/itens",
        json=_payload_item(
            id_veiculo=60,
            id_motorista=61,
            chegada_ponto="2026-09-08 13:00:00",
            inicio_real="2026-09-08 13:00:00",
            hor_ini_jor="2026-09-08 13:00:00",
            hor_fim_jor="2026-09-08 17:00:00",
        ),
    )
    assert ok.status_code == 201, ok.get_json()

# ----------------------------
# Deus seja Louvado!
# ----------------------------
"""Ocupação global EM_ANDAMENTO + baixa operacional da escala."""

from __future__ import annotations

from BackEnd.tests.conftest import auth_client


def _payload_mapa(**overrides):
    base = {
        "id_turno": 1,
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
        "hor_fim_jor": "2026-09-08 12:00:00",
        "chegada_ponto": "2026-09-08 08:10:00",
    }
    base.update(overrides)
    return base


def test_ocupacao_baixa_e_reuso(client, dal):
    auth_client(client, "1")
    # C30000 + motorista 2001
    dal.create(
        """
        INSERT INTO tb_veiculo (id_veiculo, codigo_veiculo, numero_frota, placa, ativo, id_empresa)
        VALUES (10, 10, 'C30000', 'PLA000', 1, 1)
        """
    )
    dal.create(
        """
        INSERT INTO tb_veiculo (id_veiculo, codigo_veiculo, numero_frota, placa, ativo, id_empresa)
        VALUES (11, 11, 'C30099', 'PLA099', 1, 1)
        """
    )
    dal.create(
        """
        INSERT INTO tb_motorista (id_motorista, matricula, nome, ativo)
        VALUES (10, '2001', 'João da Silva', 1)
        """
    )
    dal.create(
        """
        INSERT INTO tb_motorista (id_motorista, matricula, nome, ativo)
        VALUES (11, '2002', 'Maria Souza', 1)
        """
    )

    m1 = client.post("/api/v1/mapas", json=_payload_mapa())
    assert m1.status_code == 201
    id_reg_1 = m1.get_json()["mapa"]["id_registro"]

    i1 = client.post(
        f"/api/v1/mapas/{id_reg_1}/itens",
        json=_payload_item(id_veiculo=10, id_motorista=10),
    )
    assert i1.status_code == 201, i1.get_json()
    item1 = i1.get_json()["item"]
    id_item_1 = int(item1["id_item"])
    assert item1["status_escala"] == "EM_ANDAMENTO"

    # Viagem na escala ativa
    v = client.post(
        f"/api/v1/mapas/itens/{id_item_1}/viagens",
        json={
            "id_mapa_item": id_item_1,
            "horario_saida": "2026-09-08 09:00:00",
            "horario_chegada": "2026-09-08 10:00:00",
            "qtd_pas_ida": 2,
            "qtd_pas_volta": 1,
        },
    )
    assert v.status_code == 201, v.get_json()

    # Conflito: mesmo veículo, outro motorista (outro MAPA)
    m2 = client.post("/api/v1/mapas", json=_payload_mapa(data="2026-09-09"))
    id_reg_2 = m2.get_json()["mapa"]["id_registro"]
    conflito_v = client.post(
        f"/api/v1/mapas/{id_reg_2}/itens",
        json=_payload_item(id_veiculo=10, id_motorista=11),
    )
    assert conflito_v.status_code == 409
    assert conflito_v.get_json()["codigo"] == "conflito_veiculo"
    assert "C30000" in conflito_v.get_json()["mensagem"]
    assert "baixa" in conflito_v.get_json()["mensagem"].lower()

    # Conflito: outro veículo, mesmo motorista
    conflito_m = client.post(
        f"/api/v1/mapas/{id_reg_2}/itens",
        json=_payload_item(id_veiculo=11, id_motorista=10),
    )
    assert conflito_m.status_code == 409
    assert conflito_m.get_json()["codigo"] == "conflito_motorista"
    assert "2001" in conflito_m.get_json()["mensagem"]

    # Ocupação API
    occ = client.get("/api/v1/mapas/ocupacao")
    assert occ.status_code == 200
    body_occ = occ.get_json()
    ids_v = {int(x["id_veiculo"]) for x in body_occ["veiculos_ocupados"]}
    ids_m = {int(x["id_motorista"]) for x in body_occ["motoristas_ocupados"]}
    assert 10 in ids_v
    assert 10 in ids_m

    # Dar baixa
    baixa = client.post(
        f"/api/v1/mapas/itens/{id_item_1}/baixa",
        json={"fim_real": "2026-09-08 12:00:00", "motivo_baixa": "fim_jornada"},
    )
    assert baixa.status_code == 200, baixa.get_json()
    assert baixa.get_json()["item"]["status_escala"] == "ENCERRADA"
    assert baixa.get_json()["item"].get("baixa_em")
    assert baixa.get_json()["item"].get("fim_real")
    assert baixa.get_json()["item"].get("duracao_trabalhada_minutos") is not None

    # Nova viagem bloqueada
    v_block = client.post(
        f"/api/v1/mapas/itens/{id_item_1}/viagens",
        json={
            "id_mapa_item": id_item_1,
            "horario_saida": "2026-09-08 11:00:00",
            "horario_chegada": "2026-09-08 12:00:00",
        },
    )
    assert v_block.status_code == 409
    assert "não aceita" in v_block.get_json()["mensagem"].lower() or "baixa" in v_block.get_json()["mensagem"].lower()

    # Histórico de viagens permanece
    det = client.get(f"/api/v1/mapas/{id_reg_1}")
    assert det.status_code == 200
    itens = det.get_json()["mapa"]["itens"]
    item_det = next(i for i in itens if int(i["id_item"]) == id_item_1)
    assert item_det["status_escala"] == "ENCERRADA"
    assert len(item_det["viagens"]) == 1

    # Reuso liberado
    ok_v = client.post(
        f"/api/v1/mapas/{id_reg_2}/itens",
        json=_payload_item(id_veiculo=10, id_motorista=11),
    )
    assert ok_v.status_code == 201, ok_v.get_json()

    ok_m = client.post(
        f"/api/v1/mapas/{id_reg_1}/itens",
        json=_payload_item(
            id_veiculo=11,
            id_motorista=10,
            chegada_ponto="2026-09-08 13:00:00",
            hor_ini_jor="2026-09-08 13:00:00",
            hor_fim_jor="2026-09-08 17:00:00",
            inicio_real="2026-09-08 13:00:00",
        ),
    )
    assert ok_m.status_code == 201, ok_m.get_json()

# ----------------------------
# Deus seja Louvado!
# ----------------------------
"""Exclusividade operacional veículo/motorista + percursos sequenciais."""

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


def test_exclusividade_veiculo_motorista_e_percursos(client, dal):
    auth_client(client, "1")
    dal.create(
        """
        INSERT INTO tb_veiculo (id_veiculo, codigo_veiculo, numero_frota, placa, ativo, id_empresa)
        VALUES (40, 40, 'C30000', 'XC3000', 1, 1)
        """
    )
    dal.create(
        """
        INSERT INTO tb_veiculo (id_veiculo, codigo_veiculo, numero_frota, placa, ativo, id_empresa)
        VALUES (41, 41, 'C30114', 'XC3114', 1, 1)
        """
    )
    dal.create(
        """
        INSERT INTO tb_motorista (id_motorista, matricula, nome, ativo)
        VALUES (40, '2001', 'João Operacional', 1)
        """
    )
    dal.create(
        """
        INSERT INTO tb_motorista (id_motorista, matricula, nome, ativo)
        VALUES (41, '2002', 'Maria Livre', 1)
        """
    )

    m = client.post("/api/v1/mapas", json=_payload_mapa())
    assert m.status_code == 201
    id_reg = m.get_json()["mapa"]["id_registro"]

    # Escala C30000 + motorista 2001
    i1 = client.post(
        f"/api/v1/mapas/{id_reg}/itens",
        json=_payload_item(id_veiculo=40, id_motorista=40),
    )
    assert i1.status_code == 201, i1.get_json()
    id_item_1 = int(i1.get_json()["item"]["id_item"])
    assert i1.get_json()["item"]["status_escala"] == "EM_ANDAMENTO"

    # Outra escala com C30000 → 409
    conflito_v = client.post(
        f"/api/v1/mapas/{id_reg}/itens",
        json=_payload_item(id_veiculo=40, id_motorista=41),
    )
    assert conflito_v.status_code == 409
    body_v = conflito_v.get_json()
    assert body_v["codigo"] == "conflito_veiculo"
    assert "C30000" in body_v["mensagem"]
    assert "Dê baixa" in body_v["mensagem"]

    # Outra escala com motorista 2001 → 409
    conflito_m = client.post(
        f"/api/v1/mapas/{id_reg}/itens",
        json=_payload_item(id_veiculo=41, id_motorista=40),
    )
    assert conflito_m.status_code == 409
    body_m = conflito_m.get_json()
    assert body_m["codigo"] == "conflito_motorista"
    assert "2001" in body_m["mensagem"]
    assert "João Operacional" in body_m["mensagem"]
    assert "Dê baixa" in body_m["mensagem"]

    # Percurso 08:10–10:20 na mesma escala: permitir
    v_ok = client.post(
        f"/api/v1/mapas/itens/{id_item_1}/viagens",
        json={
            "id_mapa_item": id_item_1,
            "horario_saida": "2026-09-08 08:10:00",
            "horario_chegada": "2026-09-08 10:20:00",
            "qtd_pas_ida": 1,
            "qtd_pas_volta": 0,
        },
    )
    assert v_ok.status_code == 201, v_ok.get_json()

    # Novo percurso sobreposto 08:15–10:15 → 409
    v_sobre = client.post(
        f"/api/v1/mapas/itens/{id_item_1}/viagens",
        json={
            "id_mapa_item": id_item_1,
            "horario_saida": "2026-09-08 08:15:00",
            "horario_chegada": "2026-09-08 10:15:00",
        },
    )
    assert v_sobre.status_code == 409
    assert v_sobre.get_json()["codigo"] == "conflito_horario"

    # Baixa às 10:20
    baixa = client.post(
        f"/api/v1/mapas/itens/{id_item_1}/baixa",
        json={"fim_real": "2026-09-08 10:20:00", "motivo_baixa": "troca_veiculo"},
    )
    assert baixa.status_code == 200, baixa.get_json()
    assert baixa.get_json()["item"]["status_escala"] == "ENCERRADA"

    # Nova escala motorista 2001 + outro veículo após baixa: permitir
    i2 = client.post(
        f"/api/v1/mapas/{id_reg}/itens",
        json=_payload_item(
            id_veiculo=41,
            id_motorista=40,
            chegada_ponto="2026-09-08 10:20:00",
            inicio_real="2026-09-08 10:20:00",
            hor_ini_jor="2026-09-08 10:20:00",
            hor_fim_jor="2026-09-08 17:00:00",
        ),
    )
    assert i2.status_code == 201, i2.get_json()

    # Histórico da escala anterior permanece
    det = client.get(f"/api/v1/mapas/{id_reg}")
    assert det.status_code == 200
    item_antigo = next(
        i
        for i in det.get_json()["mapa"]["itens"]
        if int(i["id_item"]) == id_item_1
    )
    assert item_antigo["status_escala"] == "ENCERRADA"
    assert len(item_antigo["viagens"]) == 1
    assert item_antigo["viagens"][0]["horario_saida"]

    # Nova viagem na escala encerrada bloqueada
    v_block = client.post(
        f"/api/v1/mapas/itens/{id_item_1}/viagens",
        json={
            "id_mapa_item": id_item_1,
            "horario_saida": "2026-09-08 11:00:00",
            "horario_chegada": "2026-09-08 12:00:00",
        },
    )
    assert v_block.status_code == 409
    assert "baixa" in v_block.get_json()["mensagem"].lower() or "não aceita" in v_block.get_json()["mensagem"].lower()

# ----------------------------
# Deus seja Louvado!
# ----------------------------
"""Viagens sequenciais no mesmo id_mapa_item — sem sobreposição."""

from __future__ import annotations

from BackEnd.tests.conftest import auth_client


def _payload_mapa(**overrides):
    base = {
        "id_turno": 1,
        "id_empresa": 1,
        "data": "2026-09-08",
        "inicio_jornada_des": "2026-09-08 05:00:00",
        "fim_jornada_des": "2026-09-08 20:00:00",
    }
    base.update(overrides)
    return base


def _payload_item(**overrides):
    base = {
        "id_linha": 1,
        "id_veiculo": 1,
        "id_motorista": 1,
        "hor_ini_jor": "2026-09-08 08:00:00",
        "hor_fim_jor": "2026-09-08 18:00:00",
        "chegada_ponto": "2026-09-08 08:10:00",
        "inicio_real": "2026-09-08 08:10:00",
    }
    base.update(overrides)
    return base


def test_viagem_sobreposta_bloqueada_e_sequencial(client, dal):
    auth_client(client, "1")
    dal.create(
        """
        INSERT INTO tb_veiculo (id_veiculo, codigo_veiculo, numero_frota, placa, ativo, id_empresa)
        VALUES (50, 50, 'C30000', 'XC3000', 1, 1)
        """
    )
    dal.create(
        """
        INSERT INTO tb_veiculo (id_veiculo, codigo_veiculo, numero_frota, placa, ativo, id_empresa)
        VALUES (51, 51, 'C30114', 'XC3114', 1, 1)
        """
    )
    dal.create(
        """
        INSERT INTO tb_motorista (id_motorista, matricula, nome, ativo)
        VALUES (50, '2001', 'João Operacional', 1)
        """
    )

    m = client.post("/api/v1/mapas", json=_payload_mapa())
    id_reg = m.get_json()["mapa"]["id_registro"]
    i1 = client.post(
        f"/api/v1/mapas/{id_reg}/itens",
        json=_payload_item(id_veiculo=50, id_motorista=50),
    )
    assert i1.status_code == 201, i1.get_json()
    id_item = int(i1.get_json()["item"]["id_item"])

    v1 = client.post(
        f"/api/v1/mapas/itens/{id_item}/viagens",
        json={
            "id_mapa_item": id_item,
            "horario_saida": "2026-09-08 08:10:00",
            "horario_chegada": "2026-09-08 17:10:00",
        },
    )
    assert v1.status_code == 201, v1.get_json()
    id_v1 = int(v1.get_json()["viagem"]["id_viagem"])

    # Sobreposição clássica → 409, sem novo registro
    v2 = client.post(
        f"/api/v1/mapas/itens/{id_item}/viagens",
        json={
            "id_mapa_item": id_item,
            "horario_saida": "2026-09-08 08:15:00",
            "horario_chegada": "2026-09-08 10:15:00",
        },
    )
    assert v2.status_code == 409, v2.get_json()
    msg = v2.get_json()["mensagem"]
    assert "C30000" in msg
    assert "08:10" in msg
    assert "17:10" in msg
    assert v2.get_json()["codigo"] == "conflito_horario"

    det = client.get(f"/api/v1/mapas/{id_reg}")
    item = next(i for i in det.get_json()["mapa"]["itens"] if int(i["id_item"]) == id_item)
    assert len(item["viagens"]) == 1

    # Próxima exatamente no fim da anterior
    v_ok = client.post(
        f"/api/v1/mapas/itens/{id_item}/viagens",
        json={
            "id_mapa_item": id_item,
            "horario_saida": "2026-09-08 17:10:00",
            "horario_chegada": "2026-09-08 18:00:00",
        },
    )
    assert v_ok.status_code == 201, v_ok.get_json()
    id_v2 = int(v_ok.get_json()["viagem"]["id_viagem"])

    # Chegada <= saída → 422
    invalid = client.post(
        f"/api/v1/mapas/itens/{id_item}/viagens",
        json={
            "id_mapa_item": id_item,
            "horario_saida": "2026-09-08 18:00:00",
            "horario_chegada": "2026-09-08 18:00:00",
        },
    )
    assert invalid.status_code == 422
    assert invalid.get_json()["codigo"] == "horario_invalido"

    invalid2 = client.post(
        f"/api/v1/mapas/itens/{id_item}/viagens",
        json={
            "id_mapa_item": id_item,
            "horario_saida": "2026-09-08 18:30:00",
            "horario_chegada": "2026-09-08 18:00:00",
        },
    )
    assert invalid2.status_code == 422

    # Edição da própria viagem (ajustar fim) → ok
    edit_self = client.put(
        f"/api/v1/mapas/viagens/{id_v2}",
        json={
            "id_mapa_item": id_item,
            "horario_saida": "2026-09-08 17:10:00",
            "horario_chegada": "2026-09-08 17:50:00",
        },
    )
    assert edit_self.status_code == 200, edit_self.get_json()

    # Edição que sobrepõe a outra viagem → 409
    edit_other = client.put(
        f"/api/v1/mapas/viagens/{id_v2}",
        json={
            "id_mapa_item": id_item,
            "horario_saida": "2026-09-08 16:00:00",
            "horario_chegada": "2026-09-08 17:30:00",
        },
    )
    assert edit_other.status_code == 409
    assert edit_other.get_json()["codigo"] == "conflito_horario"

    # Baixa e bloqueio de nova viagem pela API
    baixa = client.post(
        f"/api/v1/mapas/itens/{id_item}/baixa",
        json={"fim_real": "2026-09-08 17:50:00"},
    )
    assert baixa.status_code == 200, baixa.get_json()

    after = client.post(
        f"/api/v1/mapas/itens/{id_item}/viagens",
        json={
            "id_mapa_item": id_item,
            "horario_saida": "2026-09-08 17:50:00",
            "horario_chegada": "2026-09-08 18:00:00",
        },
    )
    assert after.status_code == 409
    assert after.get_json()["codigo"] == "escala_encerrada"
    assert "não aceita" in after.get_json()["mensagem"].lower()

    # Histórico preservado
    det2 = client.get(f"/api/v1/mapas/{id_reg}")
    item2 = next(
        i for i in det2.get_json()["mapa"]["itens"] if int(i["id_item"]) == id_item
    )
    assert len(item2["viagens"]) == 2
    assert {int(v["id_viagem"]) for v in item2["viagens"]} == {id_v1, id_v2}

    # Após baixa, nova escala com mesmo motorista/outro veículo liberada
    i2 = client.post(
        f"/api/v1/mapas/{id_reg}/itens",
        json=_payload_item(
            id_veiculo=51,
            id_motorista=50,
            chegada_ponto="2026-09-08 17:50:00",
            inicio_real="2026-09-08 17:50:00",
            hor_ini_jor="2026-09-08 17:50:00",
            hor_fim_jor="2026-09-08 20:00:00",
        ),
    )
    assert i2.status_code == 201, i2.get_json()

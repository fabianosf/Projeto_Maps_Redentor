# ----------------------------
# Deus seja Louvado!
# ----------------------------
"""Baixa com duração + banco de horas operacional do motorista."""

from __future__ import annotations

from BackEnd.tests.conftest import auth_client, login


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
        "hor_fim_jor": "2026-09-08 17:00:00",
        "chegada_ponto": "2026-09-08 08:10:00",
    }
    base.update(overrides)
    return base


def test_cenario_troca_veiculo_banco_horas(client, dal):
    auth_client(client, "1")
    dal.create(
        """
        INSERT INTO tb_veiculo (id_veiculo, codigo_veiculo, numero_frota, placa, ativo, id_empresa)
        VALUES (20, 20, 'C30000', 'P30000', 1, 1)
        """
    )
    dal.create(
        """
        INSERT INTO tb_veiculo (id_veiculo, codigo_veiculo, numero_frota, placa, ativo, id_empresa)
        VALUES (21, 21, 'C30114', 'P30114', 1, 1)
        """
    )
    dal.create(
        """
        INSERT INTO tb_motorista (id_motorista, matricula, nome, ativo)
        VALUES (20, '2001', 'João da Silva', 1)
        """
    )

    m = client.post("/api/v1/mapas", json=_payload_mapa())
    id_reg = m.get_json()["mapa"]["id_registro"]

    i1 = client.post(
        f"/api/v1/mapas/{id_reg}/itens",
        json=_payload_item(
            id_veiculo=20,
            id_motorista=20,
            chegada_ponto="2026-09-08 08:10:00",
            inicio_real="2026-09-08 08:10:00",
        ),
    )
    assert i1.status_code == 201, i1.get_json()
    id_item_1 = int(i1.get_json()["item"]["id_item"])
    assert i1.get_json()["item"]["inicio_real"]

    # Viagem terminando às 10:20 — baixa antes deve falhar
    v = client.post(
        f"/api/v1/mapas/itens/{id_item_1}/viagens",
        json={
            "id_mapa_item": id_item_1,
            "horario_saida": "2026-09-08 09:00:00",
            "horario_chegada": "2026-09-08 10:20:00",
        },
    )
    assert v.status_code == 201, v.get_json()

    cedo = client.post(
        f"/api/v1/mapas/itens/{id_item_1}/baixa",
        json={"fim_real": "2026-09-08 10:00:00"},
    )
    assert cedo.status_code == 400
    assert "viagem" in cedo.get_json()["mensagem"].lower()

    baixa1 = client.post(
        f"/api/v1/mapas/itens/{id_item_1}/baixa",
        json={
            "fim_real": "2026-09-08 10:20:00",
            "motivo_baixa": "troca_veiculo",
        },
    )
    assert baixa1.status_code == 200, baixa1.get_json()
    item1 = baixa1.get_json()["item"]
    assert int(item1["duracao_trabalhada_minutos"]) == 130
    assert item1["duracao_trabalhada_hhmm"] == "02:10"
    assert item1["status_escala"] == "ENCERRADA"

    # Sobreposição com escala ainda aberta seria bloqueada; aqui já encerrada
    # Nova escala no mesmo instante 10:20
    i2 = client.post(
        f"/api/v1/mapas/{id_reg}/itens",
        json=_payload_item(
            id_veiculo=21,
            id_motorista=20,
            chegada_ponto="2026-09-08 10:20:00",
            inicio_real="2026-09-08 10:20:00",
            hor_ini_jor="2026-09-08 10:20:00",
            hor_fim_jor="2026-09-08 17:00:00",
        ),
    )
    assert i2.status_code == 201, i2.get_json()
    id_item_2 = int(i2.get_json()["item"]["id_item"])

    # Tentativa de sobrepor (início antes do fim da 1ª) — criar outra aberta
    # já temos i2 em andamento; tentar criar terceira sobreposta
    dal.create(
        """
        INSERT INTO tb_veiculo (id_veiculo, codigo_veiculo, numero_frota, placa, ativo, id_empresa)
        VALUES (22, 22, 'C30115', 'P30115', 1, 1)
        """
    )
    sobre = client.post(
        f"/api/v1/mapas/{id_reg}/itens",
        json=_payload_item(
            id_veiculo=22,
            id_motorista=20,
            inicio_real="2026-09-08 12:00:00",
            chegada_ponto="2026-09-08 12:00:00",
        ),
    )
    assert sobre.status_code == 409
    assert sobre.get_json()["codigo"] in (
        "conflito_sobreposicao",
        "conflito_motorista",
    )

    baixa2 = client.post(
        f"/api/v1/mapas/itens/{id_item_2}/baixa",
        json={"fim_real": "2026-09-08 17:00:00"},
    )
    assert baixa2.status_code == 200, baixa2.get_json()
    assert int(baixa2.get_json()["item"]["duracao_trabalhada_minutos"]) == 400

    # Histórico de viagens permanece
    det = client.get(f"/api/v1/mapas/{id_reg}")
    item_det = next(
        i for i in det.get_json()["mapa"]["itens"] if int(i["id_item"]) == id_item_1
    )
    assert len(item_det["viagens"]) == 1
    assert item_det["status_escala"] == "ENCERRADA"

    bh = client.get("/api/v1/motoristas/20/banco-horas?data=2026-09-08")
    assert bh.status_code == 200, bh.get_json()
    banco = bh.get_json()["banco_horas"]
    assert int(banco["total_minutos_encerrados"]) == 530
    assert banco["total_encerrado_hhmm"] == "08:50"
    assert len(banco["escalas_encerradas"]) == 2
    assert banco["controle"] == "operacional"


def test_baixa_meia_noite(client, dal):
    auth_client(client, "1")
    dal.create(
        """
        INSERT INTO tb_veiculo (id_veiculo, codigo_veiculo, numero_frota, placa, ativo, id_empresa)
        VALUES (30, 30, 'C30200', 'P30200', 1, 1)
        """
    )
    dal.create(
        """
        INSERT INTO tb_motorista (id_motorista, matricula, nome, ativo)
        VALUES (30, '3001', 'Noite Silva', 1)
        """
    )
    m = client.post(
        "/api/v1/mapas",
        json=_payload_mapa(data="2026-09-08"),
    )
    id_reg = m.get_json()["mapa"]["id_registro"]
    i = client.post(
        f"/api/v1/mapas/{id_reg}/itens",
        json=_payload_item(
            id_veiculo=30,
            id_motorista=30,
            inicio_real="2026-09-08 22:00:00",
            chegada_ponto="2026-09-08 22:00:00",
            hor_ini_jor="2026-09-08 22:00:00",
            hor_fim_jor="2026-09-09 02:00:00",
        ),
    )
    assert i.status_code == 201, i.get_json()
    id_item = int(i.get_json()["item"]["id_item"])
    b = client.post(
        f"/api/v1/mapas/itens/{id_item}/baixa",
        json={"fim_real": "2026-09-09 02:00:00"},
    )
    assert b.status_code == 200, b.get_json()
    assert int(b.get_json()["item"]["duracao_trabalhada_minutos"]) == 240


def test_banco_horas_autorizacao(client):
    # Inspetor (matrícula 3) tem acesso
    auth_client(client, "3")
    resp = client.get("/api/v1/motoristas/1/banco-horas?data=2026-09-08")
    assert resp.status_code in (200, 404)

    # Sem sessão
    client2 = client.application.test_client()
    neg = client2.get("/api/v1/motoristas/1/banco-horas?data=2026-09-08")
    assert neg.status_code == 401

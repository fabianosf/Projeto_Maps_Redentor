# ----------------------------
# Deus seja Louvado!
# ----------------------------
"""Testes Entrada/Saída — eventos C e S."""

from __future__ import annotations

from datetime import date

from BackEnd.tests.conftest import auth_client


def _criar_guia_aberta(client) -> None:
    hoje = date.today()
    data_br = f"{hoje.day:02d}/{hoje.month:02d}/{hoje.year}"
    resp = client.post(
        "/api/v1/guia",
        json={
            "numero": "GES01",
            "data": data_br,
            "id_empresa": 1,
            "id_linha": 1,
            "id_turno": 1,
            "numero_frota": "100",
            "matricula_motorista": "50001",
            "hor_ini": "05:00",
        },
    )
    assert resp.status_code == 201, resp.get_json()


def test_registrar_chegada_evento_c(client, dal):
    auth_client(client, "2")
    _criar_guia_aberta(client)

    resp = client.post(
        "/api/v1/entrada-saida/registrar",
        json={
            "evento": "C",
            "id_linha": 1,
            "carro": "100",
            "horario": "08:30",
            "temperatura": "25",
            "roleta": "1234",
        },
    )
    assert resp.status_code == 201, resp.get_json()
    body = resp.get_json()
    assert body["ok"] is True
    assert body["evento"] == "C"
    assert body["id_linha"] == 1
    assert body["id_guia"] is not None

    rows = dal.read("SELECT evento, carro FROM tb_chegada_saida ORDER BY id_cs DESC LIMIT 1")
    assert not rows.empty
    assert rows.iloc[0]["evento"] == "C"
    assert int(rows.iloc[0]["carro"]) == 3  # id_veiculo frota 100


def test_registrar_saida_evento_s(client, dal):
    auth_client(client, "2")
    _criar_guia_aberta(client)

    resp = client.post(
        "/api/v1/entrada-saida/registrar",
        json={
            "evento": "S",
            "id_linha": 1,
            "carro": "100",
            "horario": "09:15",
            "temperatura": "26",
            "roleta": "1300",
            "linha_destino": 2,
            "destino": 2,
        },
    )
    assert resp.status_code == 201, resp.get_json()
    body = resp.get_json()
    assert body["evento"] == "S"

    rows = dal.read(
        "SELECT evento, linha_destino, destino FROM tb_chegada_saida "
        "WHERE evento = 'S' ORDER BY id_cs DESC LIMIT 1"
    )
    assert not rows.empty
    assert rows.iloc[0]["evento"] == "S"
    assert int(rows.iloc[0]["linha_destino"]) == 2
    assert int(rows.iloc[0]["destino"]) == 2


def test_evento_invalido(client):
    auth_client(client, "2")
    resp = client.post(
        "/api/v1/entrada-saida/registrar",
        json={"evento": "X", "id_linha": 1, "carro": "100", "horario": "08:00"},
    )
    assert resp.status_code == 400
    assert resp.get_json()["codigo"] == "validacao"

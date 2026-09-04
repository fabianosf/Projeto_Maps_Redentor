# ----------------------------
# Deus seja Louvado!
# ----------------------------
"""Testes da Guia — criar, pesquisar, excluir."""

from __future__ import annotations

from datetime import date

from BackEnd.tests.conftest import auth_client


def _payload_guia(numero: str = "G100") -> dict:
    hoje = date.today()
    data_br = f"{hoje.day:02d}/{hoje.month:02d}/{hoje.year}"
    return {
        "numero": numero,
        "data": data_br,
        "id_empresa": 1,
        "id_linha": 1,
        "id_turno": 1,
        "numero_frota": "100",
        "matricula_motorista": "50001",
        "hor_ini": "06:00",
        # sem hor_fim — permite vínculo com entrada/saída (RF-58)
        "observacao": "teste",
    }


def test_criar_pesquisar_excluir_guia(client):
    auth_client(client, "2")  # Despachante

    criar = client.post("/api/v1/guia", json=_payload_guia("G200"))
    assert criar.status_code == 201, criar.get_json()
    data = criar.get_json()
    assert data["ok"] is True
    guia = data["guia"]
    id_guia = guia["id_guia"]
    assert guia["numero"] == "G200"

    busca = client.get("/api/v1/guia/by-numero/G200")
    assert busca.status_code == 200
    assert busca.get_json()["guia"]["id_guia"] == id_guia

    excl = client.delete(f"/api/v1/guia/{id_guia}")
    assert excl.status_code == 200
    assert excl.get_json()["ok"] is True

    busca2 = client.get("/api/v1/guia/by-numero/G200")
    assert busca2.status_code == 404


def test_criar_guia_numero_duplicado(client):
    auth_client(client, "2")
    assert client.post("/api/v1/guia", json=_payload_guia("G300")).status_code == 201
    dup = client.post("/api/v1/guia", json=_payload_guia("G300"))
    assert dup.status_code == 409
    assert dup.get_json()["codigo"] == "numero_duplicado"

# ----------------------------
# Deus seja Louvado!
# ----------------------------
"""Testes Ja E / RioCard — leituras por viagem na Guia."""

from __future__ import annotations

from datetime import date

from BackEnd.tests.conftest import auth_client


def _hoje_br() -> str:
    hoje = date.today()
    return f"{hoje.day:02d}/{hoje.month:02d}/{hoje.year}"


def test_salvar_jae_riocard_e_calcular_passageiros(client):
    auth_client(client, "2")
    data_br = _hoje_br()
    criar = client.post(
        "/api/v1/guia",
        json={
            "numero": "RJ900",
            "data": data_br,
            "id_empresa": 1,
            "id_linha": 1,
            "id_turno": 1,
            "numero_frota": "C30100",
            "matricula_motorista": "50001",
            "hor_ini": "06:00",
        },
    )
    assert criar.status_code == 201, criar.get_json()
    id_guia = criar.get_json()["guia"]["id_guia"]

    # Inicia Ja E com sugestão vazia
    ini = client.post(
        "/api/v1/guia/roletas",
        json={
            "id_guia": id_guia,
            "sentido": "ida",
            "fonte": "jae",
            "leitura_ini": 1000,
        },
    )
    assert ini.status_code == 200, ini.get_json()
    leitura = ini.get_json()["leitura"]
    assert leitura["status_leitura"] == "iniciada"
    assert leitura["passageiros"] is None
    assert leitura["leitura_ini"] == 1000

    # Finaliza
    fim = client.post(
        "/api/v1/guia/roletas",
        json={
            "id_guia": id_guia,
            "sentido": "ida",
            "fonte": "jae",
            "leitura_ini": 1000,
            "leitura_fim": 1040,
        },
    )
    assert fim.status_code == 200, fim.get_json()
    leitura = fim.get_json()["leitura"]
    assert leitura["passageiros"] == 40
    assert leitura["status_leitura"] == "finalizada"
    id_leitura = leitura["id_leitura"]

    # RioCard independente (não soma)
    rio = client.post(
        "/api/v1/guia/roletas",
        json={
            "id_guia": id_guia,
            "sentido": "ida",
            "fonte": "riocard",
            "leitura_ini": 200,
            "leitura_fim": 215,
        },
    )
    assert rio.status_code == 200
    assert rio.get_json()["leitura"]["passageiros"] == 15

    # Virada exige justificativa
    virada_bad = client.post(
        "/api/v1/guia/roletas",
        json={
            "id_guia": id_guia,
            "sentido": "volta",
            "fonte": "jae",
            "leitura_ini": 900,
            "leitura_fim": 10,
        },
    )
    assert virada_bad.status_code == 400
    assert virada_bad.get_json()["codigo"] == "virada_requer_justificativa"

    virada_ok = client.post(
        "/api/v1/guia/roletas",
        json={
            "id_guia": id_guia,
            "sentido": "volta",
            "fonte": "jae",
            "leitura_ini": 900,
            "leitura_fim": 10,
            "justificativa_virada": "contador reiniciou",
        },
    )
    assert virada_ok.status_code == 200, virada_ok.get_json()
    assert virada_ok.get_json()["leitura"]["virada"] in (1, True)
    assert virada_ok.get_json()["leitura"]["passageiros"] == (1_000_000 - 900) + 10

    hist = client.get(f"/api/v1/guia/roletas/{id_leitura}/historico")
    assert hist.status_code == 200
    assert len(hist.get_json()["historico"]) >= 2

    cons = client.get(f"/api/v1/guia/consulta?data={data_br}")
    assert cons.status_code == 200
    body = cons.get_json()
    assert body["resumo"]["ida"]["jae"] == 40
    assert body["resumo"]["ida"]["riocard"] == 15
    # Não soma Ja E + RioCard em um total único implícito
    assert body["resumo"]["ida"]["jae"] + body["resumo"]["ida"]["riocard"] == 55
    card_ida = next(v for v in body["viagens"] if v["sentido"] == "ida")
    assert card_ida["jae"]["passageiros"] == 40
    assert card_ida["riocard"]["passageiros"] == 15


def test_sugestao_leitura_viagem_anterior(client):
    auth_client(client, "2")
    data_br = _hoje_br()
    g1 = client.post(
        "/api/v1/guia",
        json={
            "numero": "RJ901",
            "data": data_br,
            "id_empresa": 1,
            "id_linha": 1,
            "id_turno": 1,
            "numero_frota": "C30100",
            "hor_ini": "06:00",
        },
    ).get_json()["guia"]["id_guia"]
    client.post(
        "/api/v1/guia/roletas",
        json={
            "id_guia": g1,
            "sentido": "ida",
            "fonte": "jae",
            "leitura_ini": 50,
            "leitura_fim": 80,
        },
    )

    sug = client.get(
        "/api/v1/guia/roletas/sugestao?id_veiculo=3&fonte=jae&sentido=ida"
    )
    assert sug.status_code == 200
    assert sug.get_json()["leitura_ini"] == 80

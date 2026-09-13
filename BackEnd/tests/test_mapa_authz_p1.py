# ----------------------------
# Deus seja Louvado!
# ----------------------------
"""P1 — responsabilidade de MAPA e escopo do Inspetor."""

from __future__ import annotations

from BackEnd.tests.conftest import auth_client


def _criar_mapa(client, *, id_empresa=1, id_turno=1, data="2026-09-15"):
    r = client.post(
        "/api/v1/mapas",
        json={
            "id_empresa": id_empresa,
            "id_turno": id_turno,
            "data": data,
            "inicio_jornada_des": "08:00",
            "fim_jornada_des": "17:00",
        },
    )
    assert r.status_code == 201, r.get_json()
    return r.get_json()["mapa"]["id_registro"]


def test_despachante_nao_edita_mapa_de_outro(client):
    auth_client(client, "2")
    id_map = _criar_mapa(client)

    auth_client(client, "4")
    r = client.post(
        f"/api/v1/mapas/{id_map}/itens",
        json={
            "id_linha": 1,
            "numero_frota": "C30114",
            "matricula": "50001",
            "hor_ini_jor": "08:10",
            "hor_fim_jor": "17:00",
            "chegada_ponto": "2026-09-15T08:10:00",
        },
    )
    assert r.status_code == 403, r.get_json()
    assert r.get_json()["codigo"] in (
        "responsabilidade_negada",
        "perfil_negado",
        "escopo_negado",
    )


def test_inspetor_403_fora_de_turno(client):
    auth_client(client, "1")
    id_map = _criar_mapa(client, id_turno=2)

    auth_client(client, "3")
    r = client.get(f"/api/v1/mapas/{id_map}")
    assert r.status_code == 403, r.get_json()


def test_admin_transfere_responsavel(client):
    auth_client(client, "1")
    id_map = _criar_mapa(client)
    r = client.post(
        f"/api/v1/mapas/{id_map}/transferir",
        json={"id_responsavel": 3, "motivo": "Cobertura de folga"},
    )
    assert r.status_code == 200, r.get_json()

    # Responsável (despachante 2) pode ler/escrever
    auth_client(client, "2")
    r2 = client.get(f"/api/v1/mapas/{id_map}")
    assert r2.status_code == 200, r2.get_json()

    # Outro despachante: sem responsabilidade e sem leitura → 403
    auth_client(client, "4")
    r3 = client.get(f"/api/v1/mapas/{id_map}")
    assert r3.status_code == 403, r3.get_json()

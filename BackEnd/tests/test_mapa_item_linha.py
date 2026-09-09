# ----------------------------
# Deus seja Louvado!
# ----------------------------
"""MAPA: cabeçalho sem frota; item com linha + veículo + motorista + horários."""

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


def test_mapa_vazio_sem_item_automatico(client):
    auth_client(client, "1")
    resp = client.post("/api/v1/mapas", json=_payload_mapa())
    assert resp.status_code == 201, resp.get_json()
    mapa = resp.get_json()["mapa"]
    assert mapa["itens"] == []
    assert mapa.get("id_linha") in (None, "", 0) or mapa["id_linha"] is None


def test_item_novo_com_linha_veiculo_motorista(client):
    auth_client(client, "1")
    cri = client.post("/api/v1/mapas", json=_payload_mapa())
    id_reg = cri.get_json()["mapa"]["id_registro"]
    item = client.post(f"/api/v1/mapas/{id_reg}/itens", json=_payload_item())
    assert item.status_code == 201, item.get_json()
    body = item.get_json()["item"]
    assert int(body["id_linha"]) == 1
    assert int(body["id_veiculo"]) == 1
    assert int(body["id_motorista"]) == 1
    assert body.get("empresa")


def test_item_legado_backfill(client, dal):
    """Simula item legado: map com id_linha + item com mesma linha."""
    auth_client(client, "1")
    dal.create(
        """
        INSERT INTO tb_map (
            id_registro, cod_map, id_usuario, id_linha, id_turno, data,
            inicio_jornada_des, fim_jornada_des
        ) VALUES (900, 900, 1, 1, 1, '2026-09-01', '2026-09-01 05:00:00', '2026-09-01 14:00:00')
        """
    )
    dal.create(
        """
        INSERT INTO tb_item_map (
            id_item, idmap, id_linha, id_veiculo, id_motorista,
            hor_ini_jor, hor_fim_jor, chegada_ponto
        ) VALUES (901, 900, 1, 1, 1,
                  '2026-09-01 08:00:00', '2026-09-01 12:00:00', '2026-09-01 08:10:00')
        """
    )
    det = client.get("/api/v1/mapas/900")
    assert det.status_code == 200, det.get_json()
    itens = det.get_json()["mapa"]["itens"]
    assert len(itens) == 1
    assert int(itens[0]["id_linha"]) == 1

    upd = client.put(
        "/api/v1/mapas/itens/901",
        json=_payload_item(
            hor_ini_jor="2026-09-01 09:00:00",
            hor_fim_jor="2026-09-01 13:00:00",
            chegada_ponto="2026-09-01 09:10:00",
        ),
    )
    assert upd.status_code == 200, upd.get_json()
    assert int(upd.get_json()["item"]["id_linha"]) == 1


def test_veiculo_repetido_mesmo_mapa(client):
    auth_client(client, "1")
    cri = client.post("/api/v1/mapas", json=_payload_mapa())
    id_reg = cri.get_json()["mapa"]["id_registro"]
    r1 = client.post(f"/api/v1/mapas/{id_reg}/itens", json=_payload_item())
    assert r1.status_code == 201
    r2 = client.post(f"/api/v1/mapas/{id_reg}/itens", json=_payload_item())
    assert r2.status_code == 409
    assert r2.get_json()["codigo"] == "conflito_veiculo"


def test_veiculo_outra_empresa_da_linha(client):
    auth_client(client, "1")
    cri = client.post("/api/v1/mapas", json=_payload_mapa())
    id_reg = cri.get_json()["mapa"]["id_registro"]
    # linha 1 = empresa 1; veiculo 2 = empresa 2
    resp = client.post(
        f"/api/v1/mapas/{id_reg}/itens",
        json=_payload_item(id_linha=1, id_veiculo=2),
    )
    assert resp.status_code == 400
    assert "empresa" in resp.get_json()["mensagem"].lower()


def test_item_sem_motorista_ou_horario(client):
    auth_client(client, "1")
    cri = client.post("/api/v1/mapas", json=_payload_mapa())
    id_reg = cri.get_json()["mapa"]["id_registro"]
    resp = client.post(
        f"/api/v1/mapas/{id_reg}/itens",
        json={
            "id_linha": 1,
            "id_veiculo": 1,
            "hor_ini_jor": "2026-09-08 08:00:00",
            "hor_fim_jor": "2026-09-08 12:00:00",
            "chegada_ponto": "2026-09-08 08:10:00",
        },
    )
    assert resp.status_code == 400

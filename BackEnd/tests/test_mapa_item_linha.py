# ----------------------------
# Deus seja Louvado!
# ----------------------------
"""MAPA: cabeçalho sem frota; item com linha + veículo + motorista + horários."""

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


def test_veiculo_outra_empresa_da_linha_permitido(client):
    """Carro ativo de outra empresa pode ser usado na linha/mapa da empresa atual."""
    auth_client(client, "1")
    cri = client.post("/api/v1/mapas", json=_payload_mapa())
    id_reg = cri.get_json()["mapa"]["id_registro"]
    # linha 1 = empresa 1; veiculo 2 = empresa 2 (C47000)
    resp = client.post(
        f"/api/v1/mapas/{id_reg}/itens",
        json=_payload_item(id_linha=1, id_veiculo=2),
    )
    assert resp.status_code == 201, resp.get_json()


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


def test_item_frota_generica_aceita(client):
    """Frota canônica C30100 (veículo seed id=3) é aceita no item."""
    auth_client(client, "1")
    cri = client.post("/api/v1/mapas", json=_payload_mapa())
    id_reg = cri.get_json()["mapa"]["id_registro"]
    resp = client.post(
        f"/api/v1/mapas/{id_reg}/itens",
        json=_payload_item(id_veiculo=3),
    )
    assert resp.status_code == 201, resp.get_json()

def test_motorista_repetido_mesmo_mapa(client, dal):
    auth_client(client, "1")
    cri = client.post("/api/v1/mapas", json=_payload_mapa())
    id_reg = cri.get_json()["mapa"]["id_registro"]
    r1 = client.post(f"/api/v1/mapas/{id_reg}/itens", json=_payload_item())
    assert r1.status_code == 201
    dal.create(
        """
        INSERT INTO tb_veiculo (id_veiculo, codigo_veiculo, numero_frota, placa, ativo, id_empresa)
        VALUES (4, 4, 'C30002', 'PLA3002', 1, 1)
        """
    )
    r2 = client.post(
        f"/api/v1/mapas/{id_reg}/itens",
        json=_payload_item(id_veiculo=4, id_motorista=1),
    )
    assert r2.status_code == 409
    assert r2.get_json()["codigo"] == "conflito_motorista"


def test_viagens_isoladas_por_item_e_motorista(client, dal):
    """Dois itens no mesmo MAPA: cada um só vê as próprias viagens + id_mapa_item."""
    auth_client(client, "1")
    dal.create(
        """
        INSERT INTO tb_veiculo (id_veiculo, codigo_veiculo, numero_frota, placa, ativo, id_empresa)
        VALUES (4, 4, 'C30002', 'PLA3002', 1, 1)
        """
    )
    dal.create(
        """
        INSERT INTO tb_motorista (id_motorista, matricula, nome, ativo)
        VALUES (2, '2001', 'João da Silva', 1)
        """
    )

    cri = client.post("/api/v1/mapas", json=_payload_mapa())
    id_reg = cri.get_json()["mapa"]["id_registro"]

    i1 = client.post(
        f"/api/v1/mapas/{id_reg}/itens",
        json=_payload_item(id_veiculo=1, id_motorista=1),
    )
    assert i1.status_code == 201, i1.get_json()
    id_item_1 = int(i1.get_json()["item"]["id_item"])

    i2 = client.post(
        f"/api/v1/mapas/{id_reg}/itens",
        json=_payload_item(
            id_linha=2,
            id_veiculo=4,
            id_motorista=2,
            hor_ini_jor="2026-09-08 08:00:00",
            hor_fim_jor="2026-09-08 17:00:00",
        ),
    )
    assert i2.status_code == 201, i2.get_json()
    id_item_2 = int(i2.get_json()["item"]["id_item"])
    assert id_item_1 != id_item_2

    # Sem id_mapa_item no body → usa o id da rota (P1)
    sem = client.post(
        f"/api/v1/mapas/itens/{id_item_1}/viagens",
        json={
            "horario_saida": "2026-09-08 09:00:00",
            "horario_chegada": "2026-09-08 10:00:00",
            "qtd_pas_ida": 1,
            "qtd_pas_volta": 0,
        },
    )
    assert sem.status_code == 201, sem.get_json()
    assert int(sem.get_json()["viagem"]["id_mapa_item"]) == id_item_1
    assert int(sem.get_json()["viagem"]["id_item_registro"]) == id_item_1

    # id_mapa_item divergente da rota → rejeita
    diverg = client.post(
        f"/api/v1/mapas/itens/{id_item_1}/viagens",
        json={
            "id_mapa_item": id_item_2,
            "horario_saida": "2026-09-08 10:00:00",
            "horario_chegada": "2026-09-08 11:00:00",
        },
    )
    assert diverg.status_code == 400

    v1 = sem  # viagem do item 1 já criada acima

    v2 = client.post(
        f"/api/v1/mapas/itens/{id_item_2}/viagens",
        json={
            "id_mapa_item": id_item_2,
            "horario_saida": "2026-09-08 11:00:00",
            "horario_chegada": "2026-09-08 12:00:00",
            "qtd_pas_ida": 3,
            "qtd_pas_volta": 1,
        },
    )
    assert v2.status_code == 201, v2.get_json()
    assert int(v2.get_json()["viagem"]["id_mapa_item"]) == id_item_2

    det = client.get(f"/api/v1/mapas/{id_reg}")
    assert det.status_code == 200
    itens = {int(i["id_item"]): i for i in det.get_json()["mapa"]["itens"]}
    assert int(itens[id_item_1]["id_mapa_item"]) == id_item_1
    assert int(itens[id_item_2]["id_mapa_item"]) == id_item_2
    assert len(itens[id_item_1]["viagens"]) == 1
    assert len(itens[id_item_2]["viagens"]) == 1
    assert int(itens[id_item_1]["viagens"][0]["id_mapa_item"]) == id_item_1
    assert int(itens[id_item_2]["viagens"][0]["id_mapa_item"]) == id_item_2
    assert int(itens[id_item_1]["id_motorista"]) == 1
    assert int(itens[id_item_2]["id_motorista"]) == 2
    assert str(itens[id_item_2].get("matricula_motorista")) == "2001"
    assert "João" in str(itens[id_item_2].get("motorista") or "")
    # Isolamento: viagem do item 1 não aparece no item 2
    ids_v1 = {int(v["id_viagem"]) for v in itens[id_item_1]["viagens"]}
    ids_v2 = {int(v["id_viagem"]) for v in itens[id_item_2]["viagens"]}
    assert ids_v1.isdisjoint(ids_v2)

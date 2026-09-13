# ----------------------------
# Deus seja Louvado!
# ----------------------------
"""Guia jornada: abertura, trechos, troca linha/carro, troca empresa, encerramento."""

from __future__ import annotations

from BackEnd.tests.conftest import auth_client


def _payload_abertura(**overrides):
    base = {
        "numero": "",
        "data": "11/09/2026",
        "id_empresa": 1,
        "id_linha": 1,
        "id_turno": 1,
        "id_veiculo": 3,
        "id_motorista": 1,
        "numero_frota": "C30100",
        "matricula_motorista": "50001",
        "hor_ini": "05:30",
        "chegada_ponto": "05:20",
        "observacao": "",
    }
    base.update(overrides)
    return base


def test_abrir_guia_cria_status_sem_trecho(client):
    auth_client(client, "1")
    resp = client.post("/api/v1/guia", json=_payload_abertura(numero="JORN01"))
    assert resp.status_code == 201, resp.get_json()
    guia = resp.get_json()["guia"]
    assert guia.get("status") == "ABERTA"
    assert guia.get("hor_fim") in (None, "")
    assert guia.get("trechos") == [] or guia.get("trechos") is None or len(guia.get("trechos") or []) == 0
    disp = (guia.get("motorista_disponibilidade") or {}).get("disponibilidade")
    assert disp == "DISPONIVEL"


def test_varios_trechos_mesma_guia(client):
    auth_client(client, "1")
    cri = client.post("/api/v1/guia", json=_payload_abertura(numero="JORN02"))
    assert cri.status_code == 201, cri.get_json()
    id_guia = int(cri.get_json()["guia"]["id_guia"])

    t1 = client.post(
        f"/api/v1/guia/{id_guia}/trechos",
        json={
            "sentido": "IDA",
            "id_linha": 1,
            "id_veiculo": 3,
            "hor_ini": "06:00",
            "hor_fim": "06:40",
            "jae_ini": 100,
            "jae_fim": 140,
            "riocard_ini": 10,
            "riocard_fim": 25,
        },
    )
    assert t1.status_code == 201, t1.get_json()
    trecho = t1.get_json()["trecho"]
    assert trecho.get("total_jae") == 40
    assert trecho.get("total_riocard") == 15
    # Não soma fontes
    assert trecho.get("total_jae") + trecho.get("total_riocard") != trecho.get("total_jae")

    t2 = client.post(
        f"/api/v1/guia/{id_guia}/trechos",
        json={
            "sentido": "VOLTA",
            "id_linha": 2,
            "numero_frota": "C30100",
            "hor_ini": "07:00",
            "hor_fim": "07:35",
            "jae_ini": 140,
            "jae_fim": 180,
            "riocard_ini": 25,
            "riocard_fim": 40,
        },
    )
    assert t2.status_code == 201, t2.get_json()

    det = client.get(f"/api/v1/guia/{id_guia}")
    assert det.status_code == 200
    trechos = det.get_json()["guia"]["trechos"]
    assert len(trechos) == 2
    assert {t.get("sentido") for t in trechos} == {"IDA", "VOLTA"}

def test_troca_carro_mesma_empresa_com_auditoria(client, dal):
    auth_client(client, "1")
    dal.create(
        "INSERT INTO tb_veiculo (id_veiculo, codigo_veiculo, numero_frota, placa, ativo, id_empresa) "
        "VALUES (80, 80, 'C30101', 'PLA0101', 1, 1)"
    )
    cri = client.post("/api/v1/guia", json=_payload_abertura(numero="JORN03"))
    id_guia = int(cri.get_json()["guia"]["id_guia"])

    alt = client.post(
        f"/api/v1/guia/{id_guia}/alteracao",
        json={
            "campo": "veiculo",
            "numero_frota": "C30101",
            "motivo": "Troca de carro por pane mecânica",
        },
    )
    assert alt.status_code == 200, alt.get_json()
    guia = alt.get_json()["guia"]
    assert guia.get("status") == "ABERTA"
    assert str(guia.get("numero_frota")) == "C30101"
    assert len(guia.get("alteracoes") or []) >= 1
    assert guia["alteracoes"][0]["campo"] == "veiculo"


def test_troca_veiculo_outra_empresa_ok_abrir_guia_exige_encerrar(client, dal):
    auth_client(client, "1")
    # Veículo empresa 1 (id 3 frota C30100)
    cri = client.post(
        "/api/v1/guia",
        json=_payload_abertura(numero="JORN04", id_empresa=1, id_veiculo=3),
    )
    assert cri.status_code == 201, cri.get_json()
    id_guia = int(cri.get_json()["guia"]["id_guia"])

    # Troca para carro cadastrado em outra empresa — permitido
    alt = client.post(
        f"/api/v1/guia/{id_guia}/alteracao",
        json={
            "campo": "veiculo",
            "numero_frota": "C47000",  # id_veiculo 2, empresa 2
            "motivo": "Troca para carro Redentor ativo",
        },
    )
    assert alt.status_code == 200, alt.get_json()
    assert str(alt.get_json()["guia"].get("numero_frota") or "").upper() == "C47000"

    # Abrir outra guia na outra empresa com mesmo motorista sem encerrar
    outra = client.post(
        "/api/v1/guia",
        json=_payload_abertura(
            numero="JORN05",
            id_empresa=2,
            id_linha=3,
            id_veiculo=2,
            numero_frota="",  # frota alfanumérica (C47000) — resolve via id_veiculo
        ),
    )
    assert outra.status_code == 409, outra.get_json()
    assert outra.get_json().get("codigo") == "empresa_diferente"

    enc = client.post(
        f"/api/v1/guia/{id_guia}/encerrar",
        json={"hor_fim": "14:00"},
    )
    assert enc.status_code == 200, enc.get_json()
    assert enc.get_json()["guia"]["status"] == "ENCERRADA"

    ok = client.post(
        "/api/v1/guia",
        json=_payload_abertura(
            numero="JORN06",
            id_empresa=2,
            id_linha=3,
            id_veiculo=2,
            numero_frota="",
        ),
    )
    assert ok.status_code == 201, ok.get_json()
    assert ok.get_json()["guia"]["status"] == "ABERTA"
    assert int(ok.get_json()["guia"]["id_empresa"]) == 2


def test_encerrar_jornada(client):
    auth_client(client, "1")
    cri = client.post("/api/v1/guia", json=_payload_abertura(numero="JORN07"))
    id_guia = int(cri.get_json()["guia"]["id_guia"])
    enc = client.post(f"/api/v1/guia/{id_guia}/encerrar", json={"hor_fim": "15:30"})
    assert enc.status_code == 200
    guia = enc.get_json()["guia"]
    assert guia["status"] == "ENCERRADA"
    assert guia.get("hor_fim")

    # Não adiciona trecho após encerrar
    t = client.post(
        f"/api/v1/guia/{id_guia}/trechos",
        json={"sentido": "IDA", "id_linha": 1, "id_veiculo": 3},
    )
    assert t.status_code == 409

# ----------------------------
# Deus seja Louvado!
# ----------------------------
"""Disponibilidade motorista, iniciar/concluir trecho, auditoria e conflito de versão."""

from __future__ import annotations

from BackEnd.tests.conftest import auth_client


def _payload(**overrides):
    base = {
        "numero": "",
        "data": "11/09/2026",
        "id_empresa": 1,
        "id_linha": 1,
        "id_turno": 1,
        "id_veiculo": 3,
        "id_motorista": 1,
        "numero_frota": "100",
        "matricula_motorista": "50001",
        "hor_ini": "05:30",
        "chegada_ponto": "05:20",
        "observacao": "",
    }
    base.update(overrides)
    return base


def test_iniciar_concluir_disponibilidade(client):
    auth_client(client, "1")
    cri = client.post("/api/v1/guia", json=_payload(numero="DISP01"))
    assert cri.status_code == 201, cri.get_json()
    guia = cri.get_json()["guia"]
    id_guia = int(guia["id_guia"])
    assert guia["motorista_disponibilidade"]["disponibilidade"] == "DISPONIVEL"

    # Adiciona e inicia trecho
    t = client.post(
        f"/api/v1/guia/{id_guia}/trechos",
        json={"sentido": "IDA", "id_linha": 1, "id_veiculo": 3, "iniciar": True, "hor_ini": "06:00"},
    )
    assert t.status_code == 201, t.get_json()
    id_trecho = int(t.get_json()["trecho"]["id_trecho"])
    assert t.get_json()["trecho"]["status"] == "EM_TRANSITO"

    det = client.get(f"/api/v1/guia/{id_guia}")
    assert det.get_json()["guia"]["motorista_disponibilidade"]["disponibilidade"] == "EM_TRANSITO"

    # Não cria outro trecho enquanto em trânsito
    bloq = client.post(
        f"/api/v1/guia/{id_guia}/trechos",
        json={"sentido": "VOLTA", "id_linha": 1, "id_veiculo": 3, "iniciar": True},
    )
    assert bloq.status_code == 409
    assert bloq.get_json()["codigo"] == "motorista_em_transito"

    # Não abre guia paralela
    paralela = client.post("/api/v1/guia", json=_payload(numero="DISP02"))
    assert paralela.status_code == 409
    assert paralela.get_json()["codigo"] in ("motorista_em_transito", "guia_aberta")

    conc = client.post(
        f"/api/v1/guia/trechos/{id_trecho}/concluir",
        json={"hor_fim": "06:40", "jae_fim": 50},
    )
    assert conc.status_code == 200, conc.get_json()
    assert conc.get_json()["trecho"]["status"] == "CONCLUIDO"

    det2 = client.get(f"/api/v1/guia/{id_guia}")
    assert det2.get_json()["guia"]["motorista_disponibilidade"]["disponibilidade"] == "DISPONIVEL"

    # Ainda não abre guia paralela — só próximo trecho na mesma
    paralela2 = client.post("/api/v1/guia", json=_payload(numero="DISP03"))
    assert paralela2.status_code == 409
    assert paralela2.get_json()["codigo"] == "guia_aberta"

    t2 = client.post(
        f"/api/v1/guia/{id_guia}/trechos",
        json={
            "sentido": "VOLTA",
            "id_linha": 1,
            "id_veiculo": 3,
            "hor_ini": "07:00",
            "iniciar": True,
            "jae_ini": 50,
        },
    )
    assert t2.status_code == 201, t2.get_json()


def test_auditoria_edicao_trecho_exige_motivo(client):
    auth_client(client, "1")
    cri = client.post("/api/v1/guia", json=_payload(numero="AUD01"))
    id_guia = int(cri.get_json()["guia"]["id_guia"])
    t = client.post(
        f"/api/v1/guia/{id_guia}/trechos",
        json={
            "sentido": "IDA",
            "id_linha": 1,
            "id_veiculo": 3,
            "hor_ini": "06:00",
            "jae_ini": 10,
            "iniciar": True,
        },
    )
    id_trecho = int(t.get_json()["trecho"]["id_trecho"])
    versao = int(t.get_json()["trecho"]["versao"])

    sem = client.put(
        f"/api/v1/guia/trechos/{id_trecho}",
        json={"jae_ini": 20, "versao": versao},
    )
    assert sem.status_code == 409
    assert sem.get_json()["codigo"] == "motivo_obrigatorio"

    ok = client.put(
        f"/api/v1/guia/trechos/{id_trecho}",
        json={
            "jae_ini": 20,
            "versao": versao,
            "motivo": "Correção de digitação da leitura",
        },
    )
    assert ok.status_code == 200, ok.get_json()
    assert int(ok.get_json()["trecho"]["jae_ini"]) == 20
    assert int(ok.get_json()["trecho"]["versao"]) == versao + 1

    det = client.get(f"/api/v1/guia/{id_guia}")
    auds = det.get_json()["guia"].get("auditorias") or []
    assert any(a.get("campo") == "jae_ini" for a in auds)


def test_conflito_versao_trecho(client):
    auth_client(client, "1")
    cri = client.post("/api/v1/guia", json=_payload(numero="VER01"))
    id_guia = int(cri.get_json()["guia"]["id_guia"])
    t = client.post(
        f"/api/v1/guia/{id_guia}/trechos",
        json={"sentido": "IDA", "id_linha": 1, "id_veiculo": 3, "hor_ini": "06:00", "iniciar": True},
    )
    id_trecho = int(t.get_json()["trecho"]["id_trecho"])
    versao = int(t.get_json()["trecho"]["versao"])

    client.put(
        f"/api/v1/guia/trechos/{id_trecho}",
        json={"hor_fim": "06:30", "versao": versao, "motivo": "Ajuste horário fim"},
    )
    conf = client.put(
        f"/api/v1/guia/trechos/{id_trecho}",
        json={"hor_fim": "06:35", "versao": versao, "motivo": "Segundo ajuste"},
    )
    assert conf.status_code == 409
    assert conf.get_json()["codigo"] == "conflito_versao"


def test_troca_carro_exige_novas_leituras(client, dal):
    auth_client(client, "1")
    dal.create(
        "INSERT INTO tb_veiculo (id_veiculo, codigo_veiculo, numero_frota, placa, ativo, id_empresa) "
        "VALUES (81, 81, '102', 'PLA0102', 1, 1)"
    )
    cri = client.post("/api/v1/guia", json=_payload(numero="CAR01"))
    id_guia = int(cri.get_json()["guia"]["id_guia"])
    t1 = client.post(
        f"/api/v1/guia/{id_guia}/trechos",
        json={
            "sentido": "IDA",
            "id_linha": 1,
            "id_veiculo": 3,
            "hor_ini": "06:00",
            "hor_fim": "06:40",
            "jae_ini": 10,
            "jae_fim": 40,
            "iniciar": True,
        },
    )
    assert t1.status_code == 201, t1.get_json()
    # Conclui implicitamente via hor_fim → CONCLUIDO
    assert t1.get_json()["trecho"]["status"] == "CONCLUIDO"

    # Novo trecho com outro carro sem leituras iniciais
    t2 = client.post(
        f"/api/v1/guia/{id_guia}/trechos",
        json={
            "sentido": "VOLTA",
            "id_linha": 1,
            "id_veiculo": 81,
            "hor_ini": "07:00",
            "iniciar": True,
        },
    )
    assert t2.status_code == 409
    assert t2.get_json()["codigo"] == "leituras_obrigatorias"

    t3 = client.post(
        f"/api/v1/guia/{id_guia}/trechos",
        json={
            "sentido": "VOLTA",
            "id_linha": 1,
            "id_veiculo": 81,
            "hor_ini": "07:00",
            "iniciar": True,
            "jae_ini": 0,
        },
    )
    assert t3.status_code == 201, t3.get_json()
    assert t3.get_json()["trecho"].get("exige_novas_leituras") is True


def test_encerrar_transferencia_empresa(client):
    auth_client(client, "1")
    cri = client.post("/api/v1/guia", json=_payload(numero="ENC01"))
    id_guia = int(cri.get_json()["guia"]["id_guia"])
    enc = client.post(
        f"/api/v1/guia/{id_guia}/encerrar",
        json={
            "hor_fim": "14:00",
            "motivo_tipo": "transferencia_empresa",
            "motivo": "Mudança para Redentor no turno da tarde",
        },
    )
    assert enc.status_code == 200, enc.get_json()
    assert enc.get_json()["guia"]["status"] == "ENCERRADA"

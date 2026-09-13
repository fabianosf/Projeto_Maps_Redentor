# ----------------------------
# Deus seja Louvado!
# ----------------------------
"""Travas motorista/carro/trecho: concorrência, cancelar, encerrar bloqueado."""

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
        "numero_frota": "C30100",
        "matricula_motorista": "50001",
        "hor_ini": "05:30:00",
        "chegada_ponto": "05:20:00",
        "observacao": "",
    }
    base.update(overrides)
    return base


def test_carro_em_transito_bloqueia_outro_trecho(client, dal):
    auth_client(client, "1")
    dal.create(
        "INSERT INTO tb_veiculo (id_veiculo, codigo_veiculo, numero_frota, placa, ativo, id_empresa) "
        "VALUES (90, 90, 'C30190', 'PLA0190', 1, 1)"
    )
    # Guia A: inicia trecho com carro 3
    a = client.post("/api/v1/guia", json=_payload(numero="TRV01"))
    id_a = int(a.get_json()["guia"]["id_guia"])
    t = client.post(
        f"/api/v1/guia/{id_a}/trechos",
        json={
            "sentido": "IDA",
            "id_linha": 1,
            "id_veiculo": 3,
            "hor_ini": "06:00:00",
            "iniciar": True,
        },
    )
    assert t.status_code == 201, t.get_json()
    assert t.get_json()["trecho"]["status"] == "EM_TRANSITO"

    # Mesmo carro não inicia em outra guia (outro motorista)
    dal.create(
        "INSERT INTO tb_motorista (id_motorista, matricula, nome, ativo) "
        "VALUES (9, '50009', 'Outro Mot', 1)"
    )
    b = client.post(
        "/api/v1/guia",
        json=_payload(
            numero="TRV02",
            id_motorista=9,
            matricula_motorista="50009",
            id_veiculo=90,
            numero_frota="C30190",
        ),
    )
    assert b.status_code == 201, b.get_json()
    id_b = int(b.get_json()["guia"]["id_guia"])
    bloq = client.post(
        f"/api/v1/guia/{id_b}/trechos",
        json={
            "sentido": "IDA",
            "id_linha": 1,
            "id_veiculo": 3,
            "hor_ini": "06:10:00",
            "iniciar": True,
        },
    )
    assert bloq.status_code == 409
    assert bloq.get_json()["codigo"] == "carro_em_transito"


def test_cancelar_libera_motorista_e_carro(client):
    auth_client(client, "1")
    cri = client.post("/api/v1/guia", json=_payload(numero="TRV03"))
    id_guia = int(cri.get_json()["guia"]["id_guia"])
    t = client.post(
        f"/api/v1/guia/{id_guia}/trechos",
        json={
            "sentido": "IDA",
            "id_linha": 1,
            "id_veiculo": 3,
            "hor_ini": "06:00:00",
            "iniciar": True,
        },
    )
    id_trecho = int(t.get_json()["trecho"]["id_trecho"])
    versao = int(t.get_json()["trecho"]["versao"])

    enc = client.post(
        f"/api/v1/guia/{id_guia}/encerrar",
        json={"hor_fim": "14:00:00", "motivo_tipo": "fim_jornada"},
    )
    assert enc.status_code == 409
    assert enc.get_json()["codigo"] == "trecho_em_transito"

    can = client.post(
        f"/api/v1/guia/trechos/{id_trecho}/cancelar",
        json={"motivo": "Pane mecânica no início da viagem", "versao": versao},
    )
    assert can.status_code == 200, can.get_json()
    assert can.get_json()["trecho"]["status"] == "CANCELADO"

    det = client.get(f"/api/v1/guia/{id_guia}")
    guia = det.get_json()["guia"]
    assert guia["status"] == "ABERTA"
    assert guia["motorista_disponibilidade"]["disponibilidade"] == "DISPONIVEL"
    assert guia["veiculo_disponibilidade"]["disponibilidade"] == "DISPONIVEL"

    # Novo trecho na mesma guia após cancelar
    t2 = client.post(
        f"/api/v1/guia/{id_guia}/trechos",
        json={
            "sentido": "IDA",
            "id_linha": 2,
            "id_veiculo": 3,
            "hor_ini": "06:30:00",
            "iniciar": True,
            "jae_ini": 10,
        },
    )
    assert t2.status_code == 201, t2.get_json()


def test_concorrencia_iniciar_trecho(client):
    auth_client(client, "1")
    cri = client.post("/api/v1/guia", json=_payload(numero="TRV04"))
    id_guia = int(cri.get_json()["guia"]["id_guia"])
    # Trecho planejado (sem iniciar)
    t = client.post(
        f"/api/v1/guia/{id_guia}/trechos",
        json={"sentido": "IDA", "id_linha": 1, "id_veiculo": 3},
    )
    assert t.status_code == 201, t.get_json()
    id_trecho = int(t.get_json()["trecho"]["id_trecho"])
    versao = int(t.get_json()["trecho"]["versao"])
    assert t.get_json()["trecho"]["status"] == "PLANEJADO"

    ok = client.post(
        f"/api/v1/guia/trechos/{id_trecho}/iniciar",
        json={"hor_ini": "2026-09-11 06:00:00", "versao": versao},
    )
    assert ok.status_code == 200, ok.get_json()
    assert ok.get_json()["trecho"]["status"] == "EM_TRANSITO"

    # Segunda tentativa com mesma versão → conflito
    conf = client.post(
        f"/api/v1/guia/trechos/{id_trecho}/iniciar",
        json={"hor_ini": "2026-09-11 06:01:00", "versao": versao},
    )
    assert conf.status_code == 409
    assert conf.get_json()["codigo"] == "conflito_versao"


def test_horario_fim_antes_inicio(client):
    auth_client(client, "1")
    cri = client.post("/api/v1/guia", json=_payload(numero="TRV05"))
    id_guia = int(cri.get_json()["guia"]["id_guia"])
    bad = client.post(
        f"/api/v1/guia/{id_guia}/trechos",
        json={
            "sentido": "IDA",
            "id_linha": 1,
            "id_veiculo": 3,
            "hor_ini": "08:00:00",
            "hor_fim": "07:00:00",
            "iniciar": True,
        },
    )
    assert bad.status_code == 400
    assert bad.get_json()["codigo"] == "horario_invalido"


def test_roleta_mesmo_carro_sugestao(client):
    auth_client(client, "1")
    cri = client.post("/api/v1/guia", json=_payload(numero="TRV06"))
    id_guia = int(cri.get_json()["guia"]["id_guia"])
    t1 = client.post(
        f"/api/v1/guia/{id_guia}/trechos",
        json={
            "sentido": "IDA",
            "id_linha": 1,
            "id_veiculo": 3,
            "hor_ini": "06:00:00",
            "hor_fim": "06:40:00",
            "jae_ini": 100,
            "jae_fim": 140,
            "iniciar": True,
        },
    )
    assert t1.status_code == 201, t1.get_json()
    id_t1 = int(t1.get_json()["trecho"]["id_trecho"])

    # Leitura vinculada ao trecho
    r = client.post(
        "/api/v1/guia/roletas",
        json={
            "id_guia": id_guia,
            "id_trecho": id_t1,
            "id_veiculo": 3,
            "sentido": "ida",
            "fonte": "jae",
            "leitura_ini": 100,
            "leitura_fim": 140,
        },
    )
    assert r.status_code == 200, r.get_json()

    sug = client.get(
        f"/api/v1/guia/roletas/sugestao?id_veiculo=3&fonte=jae&sentido=ida&id_guia={id_guia}"
    )
    assert sug.status_code == 200
    assert sug.get_json()["leitura_ini"] == 140

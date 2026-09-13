# ----------------------------
# Deus seja Louvado!
# ----------------------------
"""Regras de jornada x viagem: abertura, saída, chegada, edição e exclusão."""

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
        "hor_ini": "05:30",
        "hor_fim": "14:00",
        "chegada_ponto": "05:20",
        "observacao": "",
    }
    base.update(overrides)
    return base


def test_jornada_abre_disponivel_sem_trecho_nem_transito(client):
    auth_client(client, "1")
    # hor_fim da jornada NÃO deve criar trecho / chegada de viagem
    resp = client.post(
        "/api/v1/guia",
        json={k: v for k, v in _payload(numero="REG01").items() if k != "hor_fim"},
    )
    assert resp.status_code == 201, resp.get_json()
    guia = resp.get_json()["guia"]
    assert guia["status"] == "ABERTA"
    assert len(guia.get("trechos") or []) == 0
    assert guia["motorista_disponibilidade"]["disponibilidade"] == "DISPONIVEL"
    assert guia.get("hor_ini")
    assert guia.get("hor_fim") in (None, "")


def test_saida_real_coloca_em_transito(client):
    auth_client(client, "1")
    cri = client.post(
        "/api/v1/guia",
        json={k: v for k, v in _payload(numero="REG02").items() if k != "hor_fim"},
    )
    assert cri.status_code == 201, cri.get_json()
    id_guia = int(cri.get_json()["guia"]["id_guia"])
    assert cri.get_json()["guia"]["motorista_disponibilidade"]["disponibilidade"] == "DISPONIVEL"

    # Sem saída → pendente
    pend = client.post(
        f"/api/v1/guia/{id_guia}/trechos",
        json={"sentido": "IDA", "id_linha": 1, "id_veiculo": 3},
    )
    assert pend.status_code == 201, pend.get_json()
    assert pend.get_json()["trecho"]["status"] == "PLANEJADO"
    assert pend.get_json()["trecho"].get("hor_ini") in (None, "")
    det = client.get(f"/api/v1/guia/{id_guia}")
    assert det.get_json()["guia"]["motorista_disponibilidade"]["disponibilidade"] == "DISPONIVEL"

    # iniciar sem SAÍDA → erro
    id_t = int(pend.get_json()["trecho"]["id_trecho"])
    versao = int(pend.get_json()["trecho"]["versao"])
    sem = client.post(
        f"/api/v1/guia/trechos/{id_t}/iniciar",
        json={"versao": versao},
    )
    assert sem.status_code == 400
    assert sem.get_json()["codigo"] == "saida_obrigatoria"

    # SAÍDA real → EM_TRANSITO
    ini = client.post(
        f"/api/v1/guia/trechos/{id_t}/iniciar",
        json={"hor_ini": "06:15", "versao": versao},
    )
    assert ini.status_code == 200, ini.get_json()
    assert ini.get_json()["trecho"]["status"] == "EM_TRANSITO"
    assert ini.get_json()["trecho"].get("hor_ini")
    det2 = client.get(f"/api/v1/guia/{id_guia}")
    assert det2.get_json()["guia"]["motorista_disponibilidade"]["disponibilidade"] == "EM_TRANSITO"
    assert det2.get_json()["guia"]["veiculo_disponibilidade"]["disponibilidade"] == "EM_TRANSITO"


def test_chegada_real_conclui_e_libera(client):
    auth_client(client, "1")
    cri = client.post(
        "/api/v1/guia",
        json={k: v for k, v in _payload(numero="REG03").items() if k != "hor_fim"},
    )
    id_guia = int(cri.get_json()["guia"]["id_guia"])
    t = client.post(
        f"/api/v1/guia/{id_guia}/trechos",
        json={
            "sentido": "IDA",
            "id_linha": 1,
            "id_veiculo": 3,
            "hor_ini": "06:00",
            "iniciar": True,
        },
    )
    id_t = int(t.get_json()["trecho"]["id_trecho"])
    versao = int(t.get_json()["trecho"]["versao"])

    sem = client.post(
        f"/api/v1/guia/trechos/{id_t}/concluir",
        json={"versao": versao},
    )
    assert sem.status_code == 400
    assert sem.get_json()["codigo"] == "chegada_obrigatoria"

    # Fim da jornada NÃO serve como chegada — só hor_fim do trecho
    conc = client.post(
        f"/api/v1/guia/trechos/{id_t}/concluir",
        json={"hor_fim": "06:45", "versao": versao},
    )
    assert conc.status_code == 200, conc.get_json()
    assert conc.get_json()["trecho"]["status"] == "CONCLUIDO"
    det = client.get(f"/api/v1/guia/{id_guia}")
    guia = det.get_json()["guia"]
    assert guia["status"] == "ABERTA"
    assert guia["motorista_disponibilidade"]["disponibilidade"] == "DISPONIVEL"
    assert guia["veiculo_disponibilidade"]["disponibilidade"] == "DISPONIVEL"


def test_editar_e_excluir_pendente_sem_saida(client):
    auth_client(client, "1")
    cri = client.post(
        "/api/v1/guia",
        json={k: v for k, v in _payload(numero="REG04").items() if k != "hor_fim"},
    )
    id_guia = int(cri.get_json()["guia"]["id_guia"])
    t = client.post(
        f"/api/v1/guia/{id_guia}/trechos",
        json={"sentido": "VOLTA", "id_linha": 1, "id_veiculo": 3},
    )
    id_t = int(t.get_json()["trecho"]["id_trecho"])
    versao = int(t.get_json()["trecho"]["versao"])

    # Edição livre sem motivo
    ed = client.put(
        f"/api/v1/guia/trechos/{id_t}",
        json={"sentido": "IDA", "id_linha": 2, "versao": versao},
    )
    assert ed.status_code == 200, ed.get_json()
    assert ed.get_json()["trecho"]["status"] == "PLANEJADO"
    assert ed.get_json()["trecho"]["sentido"] == "IDA"
    versao2 = int(ed.get_json()["trecho"]["versao"])

    # Exclusão do pendente
    exc = client.delete(f"/api/v1/guia/trechos/{id_t}", json={"versao": versao2})
    assert exc.status_code == 200, exc.get_json()
    det = client.get(f"/api/v1/guia/{id_guia}")
    assert det.get_json()["guia"]["trechos"] == []


def test_em_transito_exige_cancelar_com_motivo(client):
    auth_client(client, "1")
    cri = client.post(
        "/api/v1/guia",
        json={k: v for k, v in _payload(numero="REG05").items() if k != "hor_fim"},
    )
    id_guia = int(cri.get_json()["guia"]["id_guia"])
    t = client.post(
        f"/api/v1/guia/{id_guia}/trechos",
        json={
            "sentido": "IDA",
            "id_linha": 1,
            "id_veiculo": 3,
            "hor_ini": "07:00",
            "iniciar": True,
        },
    )
    id_t = int(t.get_json()["trecho"]["id_trecho"])
    versao = int(t.get_json()["trecho"]["versao"])

    exc = client.delete(f"/api/v1/guia/trechos/{id_t}", json={"versao": versao})
    assert exc.status_code == 409
    assert exc.get_json()["codigo"] == "trecho_em_transito"

    can = client.post(
        f"/api/v1/guia/trechos/{id_t}/cancelar",
        json={"motivo": "Cliente desistiu da viagem", "versao": versao},
    )
    assert can.status_code == 200, can.get_json()
    assert can.get_json()["trecho"]["status"] == "CANCELADO"


def test_concluido_so_corrige_com_auditoria(client):
    auth_client(client, "1")
    cri = client.post(
        "/api/v1/guia",
        json={k: v for k, v in _payload(numero="REG06").items() if k != "hor_fim"},
    )
    id_guia = int(cri.get_json()["guia"]["id_guia"])
    t = client.post(
        f"/api/v1/guia/{id_guia}/trechos",
        json={
            "sentido": "IDA",
            "id_linha": 1,
            "id_veiculo": 3,
            "hor_ini": "08:00",
            "hor_fim": "08:40",
        },
    )
    id_t = int(t.get_json()["trecho"]["id_trecho"])
    versao = int(t.get_json()["trecho"]["versao"])
    assert t.get_json()["trecho"]["status"] == "CONCLUIDO"

    exc = client.delete(f"/api/v1/guia/trechos/{id_t}", json={"versao": versao})
    assert exc.status_code == 409
    assert exc.get_json()["codigo"] == "trecho_concluido"

    sem = client.put(
        f"/api/v1/guia/trechos/{id_t}",
        json={"hor_fim": "08:50", "versao": versao},
    )
    assert sem.status_code == 409
    assert sem.get_json()["codigo"] == "motivo_obrigatorio"

    ok = client.put(
        f"/api/v1/guia/trechos/{id_t}",
        json={
            "hor_fim": "08:50",
            "versao": versao,
            "motivo": "Correção de horário de chegada",
        },
    )
    assert ok.status_code == 200, ok.get_json()
    det = client.get(f"/api/v1/guia/{id_guia}")
    auds = det.get_json()["guia"].get("auditorias") or []
    assert any(a.get("campo") == "hor_fim" for a in auds)


def test_encerrar_bloqueado_com_trecho_em_transito(client):
    auth_client(client, "1")
    cri = client.post(
        "/api/v1/guia",
        json={k: v for k, v in _payload(numero="REG07").items() if k != "hor_fim"},
    )
    id_guia = int(cri.get_json()["guia"]["id_guia"])
    client.post(
        f"/api/v1/guia/{id_guia}/trechos",
        json={
            "sentido": "IDA",
            "id_linha": 1,
            "id_veiculo": 3,
            "hor_ini": "09:00",
            "iniciar": True,
        },
    )
    enc = client.post(
        f"/api/v1/guia/{id_guia}/encerrar",
        json={"hor_fim": "14:00", "motivo_tipo": "fim_jornada"},
    )
    assert enc.status_code == 409
    assert enc.get_json()["codigo"] == "trecho_em_transito"

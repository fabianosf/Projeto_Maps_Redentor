# ----------------------------
# Deus seja Louvado!
# ----------------------------
"""Testes da Guia — CRUD + consolidação Mapa/Viagens/Roleta."""

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
        "observacao": "teste",
        "roleta01_inicial": 100,
        "roleta01_final": 136,
        "roleta2_inicial": 200,
        "roleta2_final": 250,
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


def test_consulta_consolidada_por_data(client):
    auth_client(client, "2")
    payload = _payload_guia("G400")
    criar = client.post("/api/v1/guia", json=payload)
    assert criar.status_code == 201, criar.get_json()
    id_guia = criar.get_json()["guia"]["id_guia"]

    lista = client.get(f"/api/v1/guia/consulta?data={payload['data']}")
    assert lista.status_code == 200, lista.get_json()
    body = lista.get_json()
    assert body["ok"] is True
    assert "resumo" in body
    assert "viagens" in body
    assert "guias" in body
    # Legado roleta01 ainda aparece no card; resumo ida.jae é Ja E (0 sem leitura).
    assert body["resumo"]["ida"]["jae"] == 0
    assert body["resumo"]["ida"]["riocard"] == 0
    assert any(g.get("numero") == "G400" for g in body["guias"])
    ida = next(v for v in body["viagens"] if v.get("sentido") == "ida")
    assert ida.get("embarques_roleta") == 36
    assert "jae" in ida and "riocard" in ida
    assert body["status"] in {
        "sincronizado",
        "pendente",
        "divergencia",
        "manual",
        "falha",
        "atualizando",
    }

    # Mesmo contrato na coleção GET
    lista_colecao = client.get(f"/api/v1/guia?data={payload['data']}")
    assert lista_colecao.status_code == 200
    assert lista_colecao.get_json()["resumo"]["ida"]["jae"] == 0

    invalida = client.get("/api/v1/guia/consulta?data=32/13/2026")
    assert invalida.status_code == 400

    # Ajuste manual não sobrescreve roleta
    ajuste = client.post(
        f"/api/v1/guia/{id_guia}/ajuste-manual",
        json={"sentido": "ida", "embarques": 40, "justificativa": "falha catraca"},
    )
    assert ajuste.status_code == 200, ajuste.get_json()
    guia = ajuste.get_json()["guia"]
    assert guia["roleta01_ini"] == 100
    assert guia["roleta01_fim"] == 136
    assert "[AM ida=40" in (guia.get("observacao") or "")

    consolidado = client.get(
        f"/api/v1/guia/consulta?data={payload['data']}&origem=manual"
    )
    assert consolidado.status_code == 200
    body2 = consolidado.get_json()
    assert any(v.get("status") == "manual" and v.get("embarques") == 40 for v in body2["viagens"])
    assert any(
        v.get("embarques_roleta") == 36 and v.get("ajuste") is not None
        for v in body2["viagens"]
    )


def test_consulta_com_viagem_mapa(client, dal):
    auth_client(client, "2")
    hoje = date.today()
    data_sql = hoje.isoformat()
    data_br = f"{hoje.day:02d}/{hoje.month:02d}/{hoje.year}"

    # MAPA + item + viagem (fonte estrutural)
    assert dal.create(
        """
        INSERT INTO tb_map (cod_map, id_usuario, id_linha, id_turno, data, inicio_jornada_des)
        VALUES (24, 2, 1, 1, ?, ?)
        """,
        (data_sql, f"{data_sql} 06:00:00"),
    )
    id_map = int(dal.read("SELECT MAX(id_registro) AS id FROM tb_map").iloc[0]["id"])
    assert dal.create(
        """
        INSERT INTO tb_item_map (idmap, id_linha, id_veiculo, id_motorista, status_escala)
        VALUES (?, 1, 3, 1, 'EM_ANDAMENTO')
        """,
        (id_map,),
    )
    id_item = int(dal.read("SELECT MAX(id_item) AS id FROM tb_item_map").iloc[0]["id"])
    assert dal.create(
        """
        INSERT INTO tb_viagem (
            id_item_registro, horario_chegada, horario_saida, placa,
            qtd_pas_ida, qtd_pas_volta
        ) VALUES (?, ?, ?, '07:10', 30, 20)
        """,
        (id_item, f"{data_sql} 08:00:00", f"{data_sql} 07:10:00"),
    )

    # Guia com roleta do mesmo veículo/dia
    payload = _payload_guia("G500")
    payload["numero_frota"] = "100"
    assert client.post("/api/v1/guia", json=payload).status_code == 201

    resp = client.get(f"/api/v1/guia?data={data_br}")
    assert resp.status_code == 200, resp.get_json()
    body = resp.get_json()
    assert body["resumo"]["cod_map"] == 24 or body["resumo"]["titulo_mapa"]
    assert any(v.get("id_viagem") is not None for v in body["viagens"])
    assert any(v.get("mapa") and "Mapa" in str(v.get("mapa")) for v in body["viagens"])
    # Prioriza roleta (36) sobre previsto do mapa (30)
    ida = next(v for v in body["viagens"] if v["sentido"] == "ida" and v.get("id_viagem"))
    assert ida["embarques_roleta"] == 36
    assert ida["embarques"] == 36
    assert ida["origem"] == "roleta"

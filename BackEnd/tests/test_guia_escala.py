# ----------------------------
# Deus seja Louvado!
# ----------------------------
"""Testes: contexto de escala + Nova Guia + alteração auditada."""

from __future__ import annotations

from datetime import date

from BackEnd.tests.conftest import auth_client


def _data_hoje():
    hoje = date.today()
    return hoje.isoformat(), f"{hoje.day:02d}/{hoje.month:02d}/{hoje.year}"


def _criar_mapa_escala(dal, data_sql: str, frota_veiculo_id: int = 3) -> int:
    assert dal.create(
        """
        INSERT INTO tb_map (cod_map, id_usuario, id_linha, id_turno, data, inicio_jornada_des)
        VALUES (88, 2, 1, 1, ?, ?)
        """,
        (data_sql, f"{data_sql} 05:30:00"),
    )
    id_map = int(dal.read("SELECT MAX(id_registro) AS id FROM tb_map").iloc[0]["id"])
    assert dal.create(
        """
        INSERT INTO tb_item_map (
            idmap, id_linha, id_veiculo, id_motorista,
            hor_ini_jor, hor_fim_jor, chegada_ponto, status_escala
        ) VALUES (?, 1, ?, 1, ?, ?, ?, 'EM_ANDAMENTO')
        """,
        (
            id_map,
            frota_veiculo_id,
            f"{data_sql} 06:00:00",
            f"{data_sql} 14:00:00",
            f"{data_sql} 05:45:00",
        ),
    )
    id_item = int(dal.read("SELECT MAX(id_item) AS id FROM tb_item_map").iloc[0]["id"])
    assert dal.create(
        """
        INSERT INTO tb_viagem (
            id_item_registro, horario_chegada, placa, horario_saida,
            intervalo, qtd_pas_ida, qtd_pas_volta
        ) VALUES (?, ?, 'PLA0100', ?, 10, 20, 15)
        """,
        (id_item, f"{data_sql} 07:00:00", f"{data_sql} 06:30:00"),
    )
    return id_item


def test_listar_escalas_e_contexto(client, dal):
    auth_client(client, "2")
    data_sql, data_br = _data_hoje()
    id_item = _criar_mapa_escala(dal, data_sql)

    lista = client.get(f"/api/v1/guia/escalas?data={data_br}")
    assert lista.status_code == 200, lista.get_json()
    body = lista.get_json()
    assert body["ok"] is True
    assert any(m.get("cod_map") == 88 for m in body["mapas"])
    # Sem id_mapa: só mapas (carros vêm após selecionar o mapa)
    assert body["escalas"] == []

    id_mapa = body["mapas"][0]["id_registro"]
    por_mapa = client.get(f"/api/v1/guia/escalas?data={data_br}&id_mapa={id_mapa}")
    assert por_mapa.status_code == 200
    esc = por_mapa.get_json()["escalas"]
    assert any(e.get("id_item") == id_item for e in esc)
    assert all(e.get("id_mapa") == id_mapa for e in esc)
    assert any("Carro C30100" in (e.get("label") or "") or "C30100" in (e.get("label") or "") for e in esc)

    ctx = client.get(f"/api/v1/guia/contexto-escala?id_item={id_item}")
    assert ctx.status_code == 200, ctx.get_json()
    c = ctx.get_json()["contexto"]
    assert c["id_item"] == id_item
    assert c["numero_frota"] == "C30100"
    assert c["matricula_motorista"] == "50001"
    assert c["hor_ini_jor_hhmm"] == "06:00"
    assert c["hor_fim_jor_hhmm"] == "14:00"
    assert c["chegada_ponto_hhmm"] == "05:45"
    assert len(c["viagens_previstas"]) == 1


def test_criar_guia_a_partir_da_escala(client, dal):
    auth_client(client, "2")
    data_sql, data_br = _data_hoje()
    id_item = _criar_mapa_escala(dal, data_sql)

    criar = client.post(
        "/api/v1/guia",
        json={
            "numero": "GESC1",
            "data": data_br,
            "id_item_map": id_item,
            "hor_ini": "06:05",
            "hor_fim": "14:10",
            "pas_ida": 22,
            "pas_volta": 18,
            "ocorrencias": "atraso leve",
            "observacao": "ok",
            "roleta01_inicial": 10,
            "roleta01_final": 30,
            "roleta2_inicial": 1,
            "roleta2_final": 5,
        },
    )
    assert criar.status_code == 201, criar.get_json()
    guia = criar.get_json()["guia"]
    assert guia["id_item_map"] == id_item
    assert guia["id_linha"] == 1
    assert guia["id_turno"] == 1
    assert guia["numero_frota"] == "C30100"
    assert guia["matricula_motorista"] == "50001"
    assert "[IDA=22 VOLTA=18]" in (guia.get("observacao") or "")
    assert "Ocorr:atraso leve" in (guia.get("observacao") or "")


def test_criar_guia_gera_numero_automatico(client, dal):
    auth_client(client, "2")
    data_sql, data_br = _data_hoje()
    id_item = _criar_mapa_escala(dal, data_sql)

    criar = client.post(
        "/api/v1/guia",
        json={
            "data": data_br,
            "id_item_map": id_item,
            "hor_ini": "06:10",
            "hor_fim": "14:20",
        },
    )
    assert criar.status_code == 201, criar.get_json()
    guia = criar.get_json()["guia"]
    assert guia["id_item_map"] == id_item
    assert guia["numero"]
    assert len(str(guia["numero"])) <= 15
    # cod_map 88 + frota C30100 (dígitos da frota canônica)
    assert str(guia["numero"]).startswith("88")
    assert "30100" in str(guia["numero"]) or "C30100" in str(guia["numero"]).upper()

    # Segunda guia na mesma escala gera sufixo único
    criar2 = client.post(
        "/api/v1/guia",
        json={"data": data_br, "id_item_map": id_item, "hor_ini": "07:00"},
    )
    assert criar2.status_code == 201, criar2.get_json()
    assert criar2.get_json()["guia"]["numero"] != guia["numero"]


def test_alteracao_escala_com_auditoria(client, dal):
    auth_client(client, "2")
    data_sql, data_br = _data_hoje()
    id_item = _criar_mapa_escala(dal, data_sql)

    # Segundo veículo numérico para troca
    assert dal.create(
        """
        INSERT INTO tb_veiculo (codigo_veiculo, numero_frota, placa, ativo, id_empresa)
        VALUES (9, 'C30200', 'PLA0200', 1, 1)
        """
    )

    alt = client.post(
        f"/api/v1/guia/escala/{id_item}/alteracao",
        json={
            "justificativa": "quebra mecânica",
            "numero_frota": "C30200",
            "hor_ini_jor": "06:15",
        },
    )
    assert alt.status_code == 200, alt.get_json()
    ctx = alt.get_json()["contexto"]
    assert ctx["numero_frota"] == "C30200"
    assert ctx["hor_ini_jor_hhmm"] == "06:15"

    hist = dal.read(
        "SELECT * FROM tb_escala_alteracao WHERE id_item = ? ORDER BY id_alteracao",
        (id_item,),
    )
    assert not hist.empty
    campos = set(hist["campo"].tolist())
    assert "veiculo" in campos
    assert "hor_ini_jor" in campos


def test_alteracao_escala_exige_permissao(client, dal):
    auth_client(client, "3")  # Inspetor — guia escala exige permissão específica
    data_sql, _ = _data_hoje()
    id_item = _criar_mapa_escala(dal, data_sql)
    alt = client.post(
        f"/api/v1/guia/escala/{id_item}/alteracao",
        json={"justificativa": "teste", "numero_frota": "C30200"},
    )
    assert alt.status_code == 403
    assert alt.get_json()["codigo"] in ("sem_permissao", "perfil_negado", "escopo_negado")


def test_listar_mapas_filtro_data(client, dal):
    auth_client(client, "2")
    data_sql, data_br = _data_hoje()
    _criar_mapa_escala(dal, data_sql)

    todos = client.get("/api/v1/mapas")
    assert todos.status_code == 200
    filtrado = client.get(f"/api/v1/mapas?data={data_br}")
    assert filtrado.status_code == 200
    mapas = filtrado.get_json()["mapas"]
    assert any(int(m.get("cod_map") or 0) == 88 for m in mapas)

    invalido = client.get("/api/v1/mapas?data=32/13/2099")
    assert invalido.status_code == 400

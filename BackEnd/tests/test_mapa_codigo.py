# ----------------------------
# Deus seja Louvado!
# ----------------------------
"""Código sequencial de MAPA por empresa (Fut01 / Red01) + concorrência."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed

from BackEnd.mapa_service import MapaError, criar_mapa, excluir_mapa
from BackEnd.tests.conftest import auth_client


def _payload(**overrides):
    base = {
        "id_turno": 1,
        "id_empresa": 1,
        "data": "2026-09-10",
        "inicio_jornada_des": "2026-09-10 05:00:00",
        "fim_jornada_des": "2026-09-10 14:00:00",
    }
    base.update(overrides)
    return base


def test_criar_mapa_exige_empresa(client):
    auth_client(client, "1")
    resp = client.post(
        "/api/v1/mapas",
        json={
            "id_turno": 1,
            "data": "2026-09-10",
            "inicio_jornada_des": "2026-09-10 05:00:00",
        },
    )
    assert resp.status_code == 400
    body = resp.get_json()
    assert body.get("ok") is False
    assert body.get("codigo") == "empresa_obrigatoria"


def test_sequencia_independente_por_empresa(client):
    auth_client(client, "1")

    f1 = client.post("/api/v1/mapas", json=_payload(id_empresa=1))
    f2 = client.post("/api/v1/mapas", json=_payload(id_empresa=1))
    r1 = client.post("/api/v1/mapas", json=_payload(id_empresa=2))
    b1 = client.post("/api/v1/mapas", json=_payload(id_empresa=3))

    assert f1.status_code == 201, f1.get_json()
    assert f2.status_code == 201, f2.get_json()
    assert r1.status_code == 201, r1.get_json()
    assert b1.status_code == 201, b1.get_json()

    assert f1.get_json()["mapa"]["codigo_mapa"] == "Fut01"
    assert f2.get_json()["mapa"]["codigo_mapa"] == "Fut02"
    assert r1.get_json()["mapa"]["codigo_mapa"] == "Red01"
    assert b1.get_json()["mapa"]["codigo_mapa"] == "Bar01"

    lista = client.get("/api/v1/mapas?data=10/09/2026")
    assert lista.status_code == 200
    codigos = {m.get("codigo_mapa") for m in lista.get_json()["mapas"]}
    assert {"Fut01", "Fut02", "Red01", "Bar01"} <= codigos

    id_fut1 = f1.get_json()["mapa"]["id_registro"]
    det = client.get(f"/api/v1/mapas/{id_fut1}")
    assert det.status_code == 200
    assert det.get_json()["mapa"]["codigo_mapa"] == "Fut01"


def test_nao_reutiliza_codigo_apos_exclusao(client):
    auth_client(client, "1")
    a = client.post("/api/v1/mapas", json=_payload(id_empresa=1))
    b = client.post("/api/v1/mapas", json=_payload(id_empresa=1))
    assert a.status_code == 201 and b.status_code == 201
    assert a.get_json()["mapa"]["codigo_mapa"] == "Fut01"
    assert b.get_json()["mapa"]["codigo_mapa"] == "Fut02"

    id_a = a.get_json()["mapa"]["id_registro"]
    deleted = client.delete(f"/api/v1/mapas/{id_a}")
    assert deleted.status_code == 200

    c = client.post("/api/v1/mapas", json=_payload(id_empresa=1))
    assert c.status_code == 201, c.get_json()
    assert c.get_json()["mapa"]["codigo_mapa"] == "Fut03"


def test_concorrencia_gera_codigos_unicos(dal):
    """Várias criações paralelas não duplicam codigo_mapa."""
    payloads = [
        _payload(id_empresa=1, data="2026-09-11") for _ in range(8)
    ]

    def _criar(_payload_item):
        return criar_mapa(dal, 1, _payload_item)

    results = []
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = [pool.submit(_criar, p) for p in payloads]
        for fut in as_completed(futures):
            results.append(fut.result())

    codigos = []
    for r in results:
        assert not isinstance(r, MapaError), getattr(r, "mensagem", r)
        assert isinstance(r, dict)
        codigos.append(r["codigo_mapa"])

    assert len(codigos) == 8
    assert len(set(codigos)) == 8
    assert all(c.startswith("Fut") for c in codigos)


def test_get_detalhe_retorna_codigo_mapa(client):
    auth_client(client, "1")
    cri = client.post("/api/v1/mapas", json=_payload(id_empresa=2))
    assert cri.status_code == 201, cri.get_json()
    body = cri.get_json()["mapa"]
    assert body.get("codigo_mapa") == "Red01"
    assert "cod_map" in body  # id interno separado

    det = client.get(f"/api/v1/mapas/{body['id_registro']}")
    assert det.status_code == 200
    mapa = det.get_json()["mapa"]
    assert mapa.get("codigo_mapa") == "Red01"
    assert mapa.get("id_empresa") == 2


def test_formatacao_minimo_dois_digitos(dal):
    from BackEnd.mapa_service import _formatar_codigo_mapa

    assert _formatar_codigo_mapa("Red", 1) == "Red01"
    assert _formatar_codigo_mapa("Fut", 9) == "Fut09"
    assert _formatar_codigo_mapa("Bar", 10) == "Bar10"
    assert _formatar_codigo_mapa("Red", 100) == "Red100"


def test_legado_sem_codigo_recebe_ao_vincular_empresa(client, dal):
    auth_client(client, "1")
    dal.create(
        """
        INSERT INTO tb_map (
            cod_map, codigo_mapa, id_usuario, id_empresa, id_linha, id_turno,
            data, inicio_jornada_des
        ) VALUES (8001, NULL, 1, NULL, NULL, 1, '2026-09-10', '2026-09-10 05:00:00')
        """
    )
    row = dal.read("SELECT id_registro FROM tb_map WHERE cod_map = 8001")
    id_reg = int(row.iloc[0]["id_registro"])
    upd = client.put(
        f"/api/v1/mapas/{id_reg}",
        json=_payload(id_empresa=3),
    )
    assert upd.status_code == 200, upd.get_json()
    assert upd.get_json()["mapa"]["codigo_mapa"] == "Bar01"
    assert int(upd.get_json()["mapa"]["id_empresa"]) == 3


def test_excluir_nao_decrementa_seq(dal):
    m1 = criar_mapa(dal, 1, _payload(id_empresa=2))
    assert isinstance(m1, dict)
    assert m1["codigo_mapa"] == "Red01"
    excluir_mapa(dal, int(m1["id_registro"]))
    m2 = criar_mapa(dal, 1, _payload(id_empresa=2))
    assert isinstance(m2, dict)
    assert m2["codigo_mapa"] == "Red02"


def test_aloca_considera_maior_codigo_existente(dal):
    """Próximo = max(seq, maior codigo existente) + 1."""
    dal.create(
        "INSERT INTO tb_mapa_seq (id_empresa, ultimo_seq) VALUES (1, 1)"
    )
    dal.create(
        """
        INSERT INTO tb_map (
            cod_map, codigo_mapa, id_usuario, id_empresa, id_linha, id_turno,
            data, inicio_jornada_des
        ) VALUES (9001, 'Fut05', 1, 1, NULL, 1, '2026-09-10', '2026-09-10 05:00:00')
        """
    )
    m = criar_mapa(dal, 1, _payload(id_empresa=1, data="2026-09-12"))
    assert isinstance(m, dict), m
    assert m["codigo_mapa"] == "Fut06"

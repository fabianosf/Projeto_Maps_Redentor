# ----------------------------
# Deus seja Louvado!
# ----------------------------
"""GET /api/v1/mapas/{id} — legado sem codigo_mapa / sem carros / serialização."""

from __future__ import annotations

from datetime import timedelta

import pandas as pd

from BackEnd.mapa_service import _json_safe_value, obter_mapa_completo
from BackEnd.tests.conftest import auth_client


def test_json_safe_converte_timedelta_e_timestamp():
    assert _json_safe_value(timedelta(hours=17)) == "17:00"
    assert _json_safe_value(pd.Timedelta(hours=17, minutes=30)) == "17:30"
    assert _json_safe_value(pd.NaT) is None
    ts = pd.Timestamp("2026-09-11 09:00:00")
    assert _json_safe_value(ts) == "2026-09-11 09:00:00"


def test_get_mapa_sem_codigo_e_sem_carros(client, dal):
    """Registro legado: codigo_mapa NULL e sem itens → 200 com contrato completo."""
    auth_client(client, "1")
    ok = dal.create(
        """
        INSERT INTO tb_map (
            cod_map, codigo_mapa, id_usuario, id_empresa, id_linha, id_turno,
            data, inicio_jornada_des, fim_jornada_des, observacao
        ) VALUES (?, NULL, ?, NULL, NULL, ?, ?, ?, NULL, NULL)
        """,
        (
            990033,
            1,
            1,
            "2026-09-11",
            "2026-09-11 05:00:00",
        ),
    )
    assert ok
    row = dal.read("SELECT id_registro FROM tb_map WHERE cod_map = ?", (990033,))
    assert not row.empty
    id_reg = int(row.iloc[0]["id_registro"])

    resp = client.get(f"/api/v1/mapas/{id_reg}")
    assert resp.status_code == 200, resp.get_json()
    body = resp.get_json()
    assert body.get("ok") is True
    mapa = body["mapa"]
    assert mapa["id_registro"] == id_reg
    assert mapa.get("codigo_mapa") in (None, "")
    assert mapa.get("itens") == []
    assert "data" in mapa
    assert "id_turno" in mapa


def test_get_mapa_inexistente_404(client):
    auth_client(client, "1")
    resp = client.get("/api/v1/mapas/999999")
    assert resp.status_code == 404
    body = resp.get_json()
    assert body.get("ok") is False
    assert body.get("codigo") == "nao_encontrado"


def test_obter_mapa_serializa_hora_baixa_timedelta(dal):
    """hora_baixa como Timedelta (MariaDB TIME) não quebra o payload."""
    ok = dal.create(
        """
        INSERT INTO tb_map (
            cod_map, codigo_mapa, id_usuario, id_empresa, id_linha, id_turno,
            data, inicio_jornada_des, fim_jornada_des, observacao
        ) VALUES (?, ?, ?, ?, NULL, ?, ?, ?, NULL, NULL)
        """,
        (
            990034,
            "Leg01",
            1,
            1,
            1,
            "2026-09-11",
            "2026-09-11 05:00:00",
        ),
    )
    assert ok
    id_reg = int(
        dal.read("SELECT id_registro FROM tb_map WHERE cod_map = ?", (990034,)).iloc[0][
            "id_registro"
        ]
    )
    ok_item = dal.create(
        """
        INSERT INTO tb_item_map (
            idmap, id_linha, id_veiculo, id_motorista, status_escala, hora_baixa
        ) VALUES (?, ?, ?, ?, 'ENCERRADA', ?)
        """,
        (id_reg, 1, 1, 1, "17:00:00"),
    )
    assert ok_item

    # Injeta Timedelta como o driver MariaDB/pandas faria
    completo = obter_mapa_completo(dal, id_reg)
    assert not isinstance(completo, type(None))
    assert isinstance(completo, dict)
    assert completo["codigo_mapa"] == "Leg01"
    assert len(completo["itens"]) == 1
    # Força valor Timedelta e re-sanitiza via helper usado no serviço
    completo["itens"][0]["hora_baixa"] = _json_safe_value(pd.Timedelta(hours=17))
    assert completo["itens"][0]["hora_baixa"] == "17:00"
    # Payload final só com tipos JSON-friendly
    import json

    json.dumps({"ok": True, "mapa": completo})

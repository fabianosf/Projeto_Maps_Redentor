# ----------------------------
# Deus seja Louvado!
# ----------------------------
"""Validação de horário do plantão (HH:mm) no serviço de MAPA."""

from __future__ import annotations

from datetime import time

import pytest

from BackEnd.mapa_service import (
    MapaError,
    _formatar_hora_api,
    _parse_hora_plantao,
    _validar_plantao,
)


@pytest.mark.parametrize(
    "raw,esperado",
    [
        ("00:00", time(0, 0)),
        ("09:00", time(9, 0)),
        ("17:30", time(17, 30)),
        ("23:59", time(23, 59)),
        ("2026-09-08 05:00:00", time(5, 0)),
    ],
)
def test_parse_hora_plantao_aceita(raw, esperado):
    got = _parse_hora_plantao(raw, obrigatorio=True)
    assert got == esperado


@pytest.mark.parametrize(
    "raw",
    ["99", "79", "69", "24:00", "12:99", "abc", "", None, "25:00"],
)
def test_parse_hora_plantao_rejeita(raw):
    got = _parse_hora_plantao(raw, obrigatorio=True)
    assert isinstance(got, MapaError)
    assert "HH:mm" in got.mensagem


def test_validar_plantao_mesmo_dia():
    assert _validar_plantao(time(5, 0), time(14, 0)) is None
    err = _validar_plantao(time(14, 0), time(5, 0))
    assert isinstance(err, MapaError)
    err2 = _validar_plantao(time(5, 0), time(5, 0))
    assert isinstance(err2, MapaError)


def test_formatar_hora_api():
    assert _formatar_hora_api("09:00:00") == "09:00"
    assert _formatar_hora_api("2026-09-08 17:30:00") == "17:30"
    assert _formatar_hora_api(None) is None

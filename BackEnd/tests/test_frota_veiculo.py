# ----------------------------
# Deus seja Louvado!
# ----------------------------
"""Validação de frota: 47xxx | 30xxx | 13xxx (independente da empresa)."""

from __future__ import annotations

from BackEnd.cadastros_service import (
    CadastroError,
    _validar_frota_empresa,
    obter_regra_frota,
    validar_frota,
)
from BackEnd.tests.conftest import auth_client

_MSG = "47xxx"


def test_frota_valida_aceita_prefixos():
    for frota in ("47123", "30123", "13123", "47999", "30000", "13001"):
        ok = validar_frota(frota)
        assert not isinstance(ok, CadastroError), frota
        assert ok[0] == frota


def test_compat_ignora_empresa():
    """Prefixo não depende da empresa."""
    for emp in ("Redentor", "Futuro", "Barra"):
        for frota in ("47123", "30123", "13123"):
            ok = _validar_frota_empresa(frota, emp)
            assert not isinstance(ok, CadastroError), (frota, emp)


def test_rejeita_letras():
    for frota in ("C47123", "D13123", "C30123"):
        err = validar_frota(frota)
        assert isinstance(err, CadastroError), frota
        assert _MSG in err.mensagem


def test_rejeita_tamanho():
    for frota in ("4712", "471234", "30", "13"):
        err = validar_frota(frota)
        assert isinstance(err, CadastroError), frota


def test_rejeita_prefixo_fora_da_lista():
    for frota in ("12123", "99123", "40123", "00123"):
        err = validar_frota(frota)
        assert isinstance(err, CadastroError), frota
        assert _MSG in err.mensagem


def test_rejeita_especiais_e_espacos():
    for frota in ("47-123", "47 123", "47.123", ""):
        err = validar_frota(frota)
        assert isinstance(err, CadastroError), frota


def test_obter_regra_frota_defaults():
    regra = obter_regra_frota(None)
    assert regra["max_len"] == 5
    assert regra["exemplo"] == "47123"
    assert "47xxx" in regra["mensagem"]


def test_criar_veiculo_api_unico_sem_prefixo_empresa(client):
    auth_client(client, "1")
    good = client.post(
        "/api/v1/cadastros/veiculos",
        json={"numero_frota": "47123", "id_empresa": 1},
    )
    assert good.status_code in (200, 201), good.get_json()
    assert good.get_json()["veiculo"]["numero_frota"] == "47123"

    # mesma frota em outra empresa → duplicata
    dup = client.post(
        "/api/v1/cadastros/veiculos",
        json={"numero_frota": "47123", "id_empresa": 2},
    )
    assert dup.status_code in (400, 409)
    msg = dup.get_json()["mensagem"].lower()
    assert "já" in msg or "exist" in msg or "duplic" in msg

    # letras rejeitadas
    bad = client.post(
        "/api/v1/cadastros/veiculos",
        json={"numero_frota": "C47123", "id_empresa": 1},
    )
    assert bad.status_code == 400
    assert "47xxx" in bad.get_json()["mensagem"]

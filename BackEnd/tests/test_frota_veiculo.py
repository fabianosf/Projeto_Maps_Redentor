# ----------------------------
# Deus seja Louvado!
# ----------------------------
"""Validação de frota canônica: C47xxx | C30xxx | D13xxx."""

from __future__ import annotations

from BackEnd.cadastros_service import (
    CadastroError,
    _validar_frota_empresa,
    obter_regra_frota,
    validar_frota,
)
from BackEnd.tests.conftest import auth_client

_MSG = "C47xxx"


def test_frota_valida_aceita_prefixos_com_letra():
    for frota in ("C47654", "C30114", "D13450", "C47999", "C30000", "D13001"):
        ok = validar_frota(frota)
        assert not isinstance(ok, CadastroError), frota
        assert ok[0] == frota


def test_normaliza_minusculas():
    ok = validar_frota("c47654")
    assert not isinstance(ok, CadastroError)
    assert ok[0] == "C47654"


def test_empresa_prefixo_compativel():
    assert not isinstance(_validar_frota_empresa("C47654", "Redentor"), CadastroError)
    assert not isinstance(_validar_frota_empresa("C30114", "Futuro"), CadastroError)
    assert not isinstance(_validar_frota_empresa("D13450", "Barra"), CadastroError)
    err = _validar_frota_empresa("C47654", "Futuro")
    assert isinstance(err, CadastroError)
    assert "incompatível" in err.mensagem.lower() or "prefixo" in err.mensagem.lower()


def test_rejeita_sem_letra():
    for frota in ("47123", "30123", "13123"):
        err = validar_frota(frota)
        assert isinstance(err, CadastroError), frota


def test_rejeita_tamanho():
    for frota in ("C4765", "C476540", "C30", "D13"):
        err = validar_frota(frota)
        assert isinstance(err, CadastroError), frota


def test_rejeita_prefixo_fora_da_lista():
    for frota in ("C12123", "D99123", "A47123", "X30123"):
        err = validar_frota(frota)
        assert isinstance(err, CadastroError), frota


def test_obter_regra_frota_defaults():
    regra = obter_regra_frota(None)
    assert regra["max_len"] == 6
    assert regra["exemplo"] == "C47654"
    assert "C47xxx" in regra["mensagem"]


def test_criar_veiculo_api_com_letra(client):
    auth_client(client, "1")
    # empresa 2 = Redentor no sqlite seed (verificar ids)
    # sqlite: id_empresa 1 Futuro?, 2 Redentor — ver seed
    # C30001 já existe (Futuro). Criar C47654 em Redentor (id 2)
    good = client.post(
        "/api/v1/cadastros/veiculos",
        json={"numero_frota": "c47654", "id_empresa": 2},
    )
    assert good.status_code in (200, 201), good.get_json()
    assert good.get_json()["veiculo"]["numero_frota"] == "C47654"

    # sem letra rejeitada
    bad = client.post(
        "/api/v1/cadastros/veiculos",
        json={"numero_frota": "47123", "id_empresa": 2},
    )
    assert bad.status_code == 400

    # prefixo errado para empresa
    wrong = client.post(
        "/api/v1/cadastros/veiculos",
        json={"numero_frota": "D13450", "id_empresa": 2},
    )
    assert wrong.status_code == 400

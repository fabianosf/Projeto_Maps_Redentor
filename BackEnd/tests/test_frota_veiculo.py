# ----------------------------
# Deus seja Louvado!
# ----------------------------
"""Validação oficial de frota: C47 (Redentor), C30 (Futuro), D13 (Barra)."""

from __future__ import annotations

from BackEnd.cadastros_service import CadastroError, _validar_frota_empresa
from BackEnd.tests.conftest import auth_client


def test_c47654_somente_redentor():
    ok = _validar_frota_empresa("C47654", "Redentor")
    assert not isinstance(ok, CadastroError)
    assert ok[0] == "C47654"

    for emp in ("Futuro", "Barra"):
        err = _validar_frota_empresa("C47654", emp)
        assert isinstance(err, CadastroError)


def test_c30114_somente_futuro():
    ok = _validar_frota_empresa("C30114", "Futuro")
    assert not isinstance(ok, CadastroError)

    for emp in ("Redentor", "Barra"):
        err = _validar_frota_empresa("C30114", emp)
        assert isinstance(err, CadastroError)


def test_d13450_somente_barra():
    ok = _validar_frota_empresa("D13450", "Barra")
    assert not isinstance(ok, CadastroError)

    for emp in ("Futuro", "Redentor"):
        err = _validar_frota_empresa("D13450", emp)
        assert isinstance(err, CadastroError)


def test_c30450_rejeitado_barra_aceito_futuro():
    err = _validar_frota_empresa("C30450", "Barra")
    assert isinstance(err, CadastroError)
    assert "D13" in err.mensagem

    ok = _validar_frota_empresa("C30450", "Futuro")
    assert not isinstance(ok, CadastroError)


def test_mensagens_especificas():
    assert "C47" in _validar_frota_empresa("", "Redentor").mensagem  # type: ignore[union-attr]
    assert "C30" in _validar_frota_empresa("C47", "Futuro").mensagem  # type: ignore[union-attr]
    assert "D13" in _validar_frota_empresa("C30450", "Barra").mensagem  # type: ignore[union-attr]


def test_criar_veiculo_api_respeita_padrao(client):
    auth_client(client, "1")
    # Futuro = id_empresa 1
    bad = client.post(
        "/api/v1/cadastros/veiculos",
        json={"numero_frota": "C47654", "id_empresa": 1},
    )
    assert bad.status_code == 400
    assert "C30" in bad.get_json()["mensagem"]

    good = client.post(
        "/api/v1/cadastros/veiculos",
        json={"numero_frota": "C30114", "id_empresa": 1},
    )
    assert good.status_code in (200, 201), good.get_json()
    assert good.get_json()["veiculo"]["numero_frota"] == "C30114"

    # Redentor = id_empresa 2
    red = client.post(
        "/api/v1/cadastros/veiculos",
        json={"numero_frota": "C47654", "id_empresa": 2},
    )
    assert red.status_code in (200, 201), red.get_json()

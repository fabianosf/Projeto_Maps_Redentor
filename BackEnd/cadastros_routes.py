# ----------------------------
# Deus seja Louvado!
# ----------------------------

"""Endpoints REST — /api/v1/cadastros (dados mestres operacionais)."""

from __future__ import annotations

from flask import Blueprint, g, jsonify, request

from .auth_middleware import json_error, require_mapa_access, require_session
from .cadastros_service import CadastroError, criar_veiculo, listar_cadastros_mestres

cadastros_bp = Blueprint("cadastros", __name__, url_prefix="/api/v1/cadastros")


@cadastros_bp.get("")
@require_session
def cadastros_mestres():
    return jsonify({"ok": True, "cadastros": listar_cadastros_mestres(g.dal)}), 200


@cadastros_bp.post("/veiculos")
@require_mapa_access
def post_veiculo():
    """Cadastra veículo (frota) — cadastro independente; id_empresa opcional."""
    body = request.get_json(silent=True) or {}
    numero_frota = str(body.get("numero_frota", body.get("frota", ""))).strip()
    id_empresa = body.get("id_empresa")

    resultado = criar_veiculo(
        g.dal,
        numero_frota=numero_frota,
        id_empresa=id_empresa,
    )
    if isinstance(resultado, CadastroError):
        status = 409 if resultado.codigo == "frota_duplicada" else 400
        return json_error(resultado.mensagem, status, resultado.codigo)
    return jsonify({"ok": True, "veiculo": resultado}), 201

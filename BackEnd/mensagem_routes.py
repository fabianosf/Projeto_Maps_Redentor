# ----------------------------
# Deus seja Louvado!
# ----------------------------

"""Endpoints REST — /api/v1/mensagem/* (Tela 07)."""

from __future__ import annotations

from flask import Blueprint, g, jsonify, request

from .auth_middleware import json_error, require_session
from .mensagem_service import MensagemError, listar_tipos_avaria, registrar_avaria

mensagem_bp = Blueprint("mensagem", __name__, url_prefix="/api/v1/mensagem")


@mensagem_bp.get("/tipos-avaria")
@require_session
def tipos_avaria():
    tipos = listar_tipos_avaria(g.dal)
    return jsonify({"ok": True, "tipos": tipos}), 200


@mensagem_bp.post("")
@require_session
def criar_mensagem():
    body = request.get_json(silent=True) or {}
    try:
        id_tip = int(body.get("id_tip", 0))
    except (TypeError, ValueError):
        id_tip = 0
    resultado = registrar_avaria(
        g.dal,
        g.auth_usuario.id_usuario,
        str(body.get("numero_frota", body.get("carro", ""))),
        id_tip,
        str(body.get("texto", "")),
    )
    if isinstance(resultado, MensagemError):
        return json_error(resultado.mensagem, 400, resultado.codigo)
    return jsonify({"ok": True, "avaria": resultado, "mensagem": "Mensagem enviada com sucesso."}), 201

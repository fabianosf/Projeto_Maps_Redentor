# ----------------------------
# Deus seja Louvado!
# ----------------------------

"""Endpoints REST — /api/v1/entrada-saida/*"""

from __future__ import annotations

from flask import Blueprint, g, jsonify, request

from .auth_middleware import json_error, require_session
from .entrada_saida_service import (
    EntradaSaidaError,
    listar_linhas_saida_referencia,
    obter_contexto_entrada_saida,
    registrar_chegada_saida,
)

entrada_saida_bp = Blueprint("entrada_saida", __name__, url_prefix="/api/v1/entrada-saida")


@entrada_saida_bp.get("/contexto")
@require_session
def contexto():
    usuario = g.auth_usuario
    resultado = obter_contexto_entrada_saida(g.dal, usuario.id_usuario)
    if isinstance(resultado, EntradaSaidaError):
        return json_error(resultado.mensagem, 400, resultado.codigo)
    return jsonify({"ok": True, **resultado}), 200


@entrada_saida_bp.get("/linhas-saida")
@require_session
def linhas_saida():
    usuario = g.auth_usuario
    id_linha = request.args.get("id_linha", "").strip()
    if not id_linha.isdigit():
        return json_error("Informe id_linha válido.", 400, "validacao")
    resultado = listar_linhas_saida_referencia(
        g.dal, usuario.id_usuario, int(id_linha)
    )
    if isinstance(resultado, EntradaSaidaError):
        return json_error(resultado.mensagem, 400, resultado.codigo)
    return jsonify({"ok": True, "linhas": resultado}), 200


@entrada_saida_bp.post("/registrar")
@require_session
def registrar():
    usuario = g.auth_usuario
    body = request.get_json(silent=True) or {}
    resultado = registrar_chegada_saida(g.dal, usuario.id_usuario, body)
    if isinstance(resultado, EntradaSaidaError):
        return json_error(resultado.mensagem, 400, resultado.codigo)
    return jsonify({"ok": True, **resultado, "mensagem": "Registro salvo com sucesso."}), 201

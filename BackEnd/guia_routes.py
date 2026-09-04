# ----------------------------
# Deus seja Louvado!
# ----------------------------

"""Endpoints REST — /api/v1/guia/* (Tela 08)."""

from __future__ import annotations

from flask import Blueprint, g, jsonify, request

from .auth_middleware import json_error, require_session
from .guia_service import (
    GuiaError,
    atualizar_guia,
    buscar_por_numero,
    criar_guia,
    excluir_guia,
)

guia_bp = Blueprint("guia", __name__, url_prefix="/api/v1/guia")


@guia_bp.get("/by-numero/<numero>")
@require_session
def get_by_numero(numero: str):
    resultado = buscar_por_numero(g.dal, numero)
    if isinstance(resultado, GuiaError):
        status = 404 if resultado.codigo == "nao_encontrado" else 400
        return json_error(resultado.mensagem, status, resultado.codigo)
    return jsonify({"ok": True, "guia": resultado}), 200


@guia_bp.post("")
@require_session
def create_guia():
    body = request.get_json(silent=True) or {}
    resultado = criar_guia(g.dal, body)
    if isinstance(resultado, GuiaError):
        status = 409 if resultado.codigo == "numero_duplicado" else 400
        return json_error("Não foi possível cadastrar a guia!", status, resultado.codigo)
    return jsonify(
        {"ok": True, "guia": resultado, "mensagem": "Guia cadastrada com sucesso!"}
    ), 201


@guia_bp.put("/<int:id_guia>")
@require_session
def update_guia(id_guia: int):
    body = request.get_json(silent=True) or {}
    resultado = atualizar_guia(g.dal, id_guia, body)
    if isinstance(resultado, GuiaError):
        status = 404 if resultado.codigo == "nao_encontrado" else 400
        if resultado.codigo == "numero_duplicado":
            status = 409
        return json_error(resultado.mensagem, status, resultado.codigo)
    return jsonify({"ok": True, "guia": resultado, "mensagem": "Guia atualizada com sucesso."}), 200


@guia_bp.delete("/<int:id_guia>")
@require_session
def delete_guia(id_guia: int):
    erro = excluir_guia(g.dal, id_guia)
    if erro:
        status = 409 if erro.codigo == "guia_em_uso" else 404
        return json_error(erro.mensagem, status, erro.codigo)
    return jsonify({"ok": True, "mensagem": "Guia excluída com sucesso."}), 200

# ----------------------------
# Deus seja Louvado!
# ----------------------------

"""Endpoints REST do módulo MAPA — /api/v1/mapa/* (RF-MAP-RN)."""

from __future__ import annotations

from flask import Blueprint, g, jsonify, request

from .auth_middleware import json_error, require_mapa_access
from .auth_service import UsuarioAuth
from .mapa_service import (
    MapaError,
    atualizar_item_map,
    atualizar_mapa,
    atualizar_viagem,
    criar_item_map,
    criar_mapa,
    criar_viagem,
    excluir_item_map,
    excluir_mapa,
    excluir_viagem,
    listar_cadastros_mestres,
    listar_mapas,
    obter_indicadores,
    obter_mapa_completo,
)

mapa_bp = Blueprint("mapa", __name__, url_prefix="/api/v1/mapa")


def _dal():
    return g.dal


@mapa_bp.get("/cadastros")
@require_mapa_access
def cadastros_mestres():
    return jsonify({"ok": True, "cadastros": listar_cadastros_mestres(_dal())}), 200


@mapa_bp.get("/indicadores")
@require_mapa_access
def indicadores():
    id_linha_raw = request.args.get("id_linha")
    id_linha = None
    if id_linha_raw not in (None, ""):
        try:
            id_linha = int(id_linha_raw)
        except (TypeError, ValueError):
            return json_error("Linha inválida.", 400, "validacao")
    resultado = obter_indicadores(_dal(), id_linha)
    if isinstance(resultado, MapaError):
        status = 404 if resultado.codigo == "nao_encontrado" else 400
        return json_error(resultado.mensagem, status, resultado.codigo)
    return jsonify({"ok": True, "indicadores": resultado}), 200


@mapa_bp.get("")
@require_mapa_access
def list_maps():
    return jsonify({"ok": True, "mapas": listar_mapas(_dal())}), 200


@mapa_bp.get("/<int:id_registro>")
@require_mapa_access
def get_map(id_registro: int):
    resultado = obter_mapa_completo(_dal(), id_registro)
    if isinstance(resultado, MapaError):
        return json_error(resultado.mensagem, 404, resultado.codigo)
    return jsonify({"ok": True, "mapa": resultado}), 200


@mapa_bp.post("")
@require_mapa_access
def create_map():
    usuario: UsuarioAuth = g.auth_usuario
    body = request.get_json(silent=True) or {}
    resultado = criar_mapa(_dal(), usuario.id_usuario, body)
    if isinstance(resultado, MapaError):
        status = 400
        if resultado.codigo == "cod_map_esgotado":
            status = 409
        return json_error(resultado.mensagem, status, resultado.codigo)
    return jsonify({"ok": True, "mapa": resultado}), 201


@mapa_bp.put("/<int:id_registro>")
@require_mapa_access
def update_map(id_registro: int):
    body = request.get_json(silent=True) or {}
    resultado = atualizar_mapa(_dal(), id_registro, body)
    if isinstance(resultado, MapaError):
        status = 404 if resultado.codigo == "nao_encontrado" else 400
        return json_error(resultado.mensagem, status, resultado.codigo)
    return jsonify({"ok": True, "mapa": resultado}), 200


@mapa_bp.delete("/<int:id_registro>")
@require_mapa_access
def delete_map(id_registro: int):
    erro = excluir_mapa(_dal(), id_registro)
    if erro:
        return json_error(erro.mensagem, 404, erro.codigo)
    return jsonify({"ok": True}), 200


@mapa_bp.post("/<int:id_registro>/itens")
@require_mapa_access
def create_item(id_registro: int):
    body = request.get_json(silent=True) or {}
    resultado = criar_item_map(_dal(), id_registro, body)
    if isinstance(resultado, MapaError):
        status = 404 if resultado.codigo == "nao_encontrado" else 400
        return json_error(resultado.mensagem, status, resultado.codigo)
    return jsonify({"ok": True, "item": resultado}), 201


@mapa_bp.put("/itens/<int:id_item>")
@require_mapa_access
def update_item(id_item: int):
    body = request.get_json(silent=True) or {}
    resultado = atualizar_item_map(_dal(), id_item, body)
    if isinstance(resultado, MapaError):
        status = 404 if resultado.codigo == "nao_encontrado" else 400
        return json_error(resultado.mensagem, status, resultado.codigo)
    return jsonify({"ok": True, "item": resultado}), 200


@mapa_bp.delete("/itens/<int:id_item>")
@require_mapa_access
def delete_item(id_item: int):
    erro = excluir_item_map(_dal(), id_item)
    if erro:
        return json_error(erro.mensagem, 404, erro.codigo)
    return jsonify({"ok": True}), 200


@mapa_bp.post("/itens/<int:id_item>/viagens")
@require_mapa_access
def create_trip(id_item: int):
    body = request.get_json(silent=True) or {}
    resultado = criar_viagem(_dal(), id_item, body)
    if isinstance(resultado, MapaError):
        status = 404 if resultado.codigo == "nao_encontrado" else 400
        return json_error(resultado.mensagem, status, resultado.codigo)
    return jsonify({"ok": True, "viagem": resultado}), 201


@mapa_bp.put("/viagens/<int:id_viagem>")
@require_mapa_access
def update_trip(id_viagem: int):
    body = request.get_json(silent=True) or {}
    resultado = atualizar_viagem(_dal(), id_viagem, body)
    if isinstance(resultado, MapaError):
        status = 404 if resultado.codigo == "nao_encontrada" else 400
        return json_error(resultado.mensagem, status, resultado.codigo)
    return jsonify({"ok": True, "viagem": resultado}), 200


@mapa_bp.delete("/viagens/<int:id_viagem>")
@require_mapa_access
def delete_trip(id_viagem: int):
    erro = excluir_viagem(_dal(), id_viagem)
    if erro:
        return json_error(erro.mensagem, 404, erro.codigo)
    return jsonify({"ok": True}), 200

# ----------------------------
# Deus seja Louvado!
# ----------------------------

"""Endpoints — /api/v1/indicadores-config/* (cadastro indicador × perfil)."""

from __future__ import annotations

from flask import Blueprint, g, jsonify, request

from .auth_middleware import json_error, require_config_access, require_session
from .indicadores_config_service import (
    ServiceError,
    listar_indicadores,
    listar_indicadores_com_vinculo,
    listar_indicadores_permitidos,
    listar_perfis,
    salvar_vinculos_indicadores,
)

indicadores_config_bp = Blueprint(
    "indicadores_config",
    __name__,
    url_prefix="/api/v1/indicadores-config",
)


@indicadores_config_bp.get("/indicadores")
@require_config_access
def get_indicadores_catalogo():
    """RF-52 — lista completa de tb_indicador."""
    return jsonify({"ok": True, "indicadores": listar_indicadores(g.dal)}), 200


@indicadores_config_bp.get("/perfis")
@require_config_access
def get_perfis():
    return jsonify({"ok": True, "perfis": listar_perfis(g.dal)}), 200


@indicadores_config_bp.get("/me/indicadores")
@require_session
def get_indicadores_permitidos_sessao():
    """
    RN-08 — indicadores habilitados para o perfil logado.
    Não aceita id_perfil/codigo_perfil na URL/query (anti-manipulação).
    """
    # Qualquer tentativa de forçar outro perfil via query é ignorada.
    _ = request.args.get("id_perfil")
    _ = request.args.get("codigo_perfil")
    usuario = g.auth_usuario
    indicadores = listar_indicadores_permitidos(g.dal, int(usuario.codigo_perfil))
    return jsonify({"ok": True, "indicadores": indicadores}), 200


@indicadores_config_bp.get("/<int:id_perfil>/indicadores")
@require_config_access
def get_indicadores_vinculo(id_perfil: int):
    resultado = listar_indicadores_com_vinculo(g.dal, id_perfil)
    if isinstance(resultado, ServiceError):
        status = 404 if resultado.codigo == "nao_encontrado" else 400
        return json_error(resultado.mensagem, status, resultado.codigo)
    return jsonify({"ok": True, "indicadores": resultado}), 200


@indicadores_config_bp.put("/<int:id_perfil>/indicadores")
@require_config_access
def put_indicadores_vinculo(id_perfil: int):
    body = request.get_json(silent=True) or {}
    id_inds = body.get("id_inds") or []
    if not isinstance(id_inds, list):
        return json_error("Lista de indicadores inválida.", 400, "validacao")

    resultado = salvar_vinculos_indicadores(g.dal, id_perfil, id_inds)
    if isinstance(resultado, ServiceError):
        status = 404 if resultado.codigo == "nao_encontrado" else 400
        return json_error(resultado.mensagem, status, resultado.codigo)

    return jsonify(
        {
            "ok": True,
            "mensagem": "Vínculos de perfil e indicadores salvos com sucesso.",
        }
    ), 200

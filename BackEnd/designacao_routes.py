# ----------------------------
# Deus seja Louvado!
# ----------------------------

"""Endpoints REST — DesignacaoOperacional /api/v1/designacoes/*"""

from __future__ import annotations

from flask import Blueprint, g, jsonify, request

from .auth_middleware import json_error, require_admin, require_session
from .auth_service import UsuarioAuth
from .constants import PERFIL_ADMIN
from .designacao_service import (
    ServiceError,
    criar_designacao,
    listar_historico,
    obter_ativa,
    transferir_designacao,
)

designacoes_bp = Blueprint(
    "designacoes", __name__, url_prefix="/api/v1/designacoes"
)


def _dal():
    return g.dal


def _status_erro(codigo: str) -> int:
    if codigo == "nao_encontrado":
        return 404
    if codigo in ("conflito_ativa",):
        return 409
    if codigo in ("perfil_negado",):
        return 403
    return 400


def _resolver_id_usuario_consulta() -> int | tuple:
    """Despachante: próprio id. Admin: ?id_usuario= obrigatório para outro."""
    usuario: UsuarioAuth = g.auth_usuario
    q = request.args.get("id_usuario")
    if usuario.codigo_perfil == PERFIL_ADMIN:
        if q is None or str(q).strip() == "":
            return json_error(
                "Informe id_usuario do despachante.",
                400,
                "validacao",
            )
        try:
            return int(q)
        except (TypeError, ValueError):
            return json_error("id_usuario inválido.", 400, "validacao")
    if q is not None and str(q).strip() != "":
        try:
            alvo = int(q)
        except (TypeError, ValueError):
            return json_error("id_usuario inválido.", 400, "validacao")
        if alvo != usuario.id_usuario:
            return json_error("Operação não autorizada.", 403, "perfil_negado")
        return alvo
    return usuario.id_usuario


@designacoes_bp.get("/ativa")
@require_session
def get_ativa():
    resolved = _resolver_id_usuario_consulta()
    if not isinstance(resolved, int):
        return resolved
    ativa = obter_ativa(_dal(), resolved)
    return jsonify({"ok": True, "designacao_ativa": ativa}), 200


@designacoes_bp.get("/historico")
@require_session
def get_historico():
    resolved = _resolver_id_usuario_consulta()
    if not isinstance(resolved, int):
        return resolved
    itens = listar_historico(_dal(), resolved)
    return jsonify({"ok": True, "designacoes": itens}), 200


@designacoes_bp.post("")
@require_admin
def post_criar():
    body = request.get_json(silent=True) or {}
    admin: UsuarioAuth = g.auth_usuario
    resultado = criar_designacao(
        _dal(),
        id_usuario=body.get("id_usuario"),
        id_empresa=body.get("id_empresa"),
        id_turno=body.get("id_turno"),
        data=body.get("data"),
        inicio=body.get("inicio"),
        id_linha=body.get("id_linha"),
        id_veiculo=body.get("id_veiculo"),
        id_admin=admin.id_usuario,
    )
    if isinstance(resultado, ServiceError):
        return json_error(resultado.mensagem, _status_erro(resultado.codigo), resultado.codigo)
    return jsonify({"ok": True, "designacao": resultado}), 201


@designacoes_bp.post("/transferir")
@require_admin
def post_transferir():
    body = request.get_json(silent=True) or {}
    admin: UsuarioAuth = g.auth_usuario
    resultado = transferir_designacao(
        _dal(),
        id_usuario=body.get("id_usuario"),
        id_empresa=body.get("id_empresa"),
        id_turno=body.get("id_turno"),
        data=body.get("data"),
        inicio=body.get("inicio"),
        id_linha=body.get("id_linha"),
        id_veiculo=body.get("id_veiculo"),
        fim=body.get("fim"),
        id_admin=admin.id_usuario,
    )
    if isinstance(resultado, ServiceError):
        return json_error(resultado.mensagem, _status_erro(resultado.codigo), resultado.codigo)
    return jsonify({"ok": True, "designacao": resultado}), 200

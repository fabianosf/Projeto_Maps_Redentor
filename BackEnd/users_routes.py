# ----------------------------
# Deus seja Louvado!
# ----------------------------

"""Endpoints REST de usuários — /api/v1/users/* (RF-RN-013..015)."""

from __future__ import annotations

from flask import Blueprint, g, jsonify, request

from .auth_middleware import json_error, require_admin, require_config_access
from .dal_factory import get_erp_dal_instance
from .erp_service import ErpError, consultar_funcionario_erp
from .users_service import (
    ServiceError,
    atualizar_perfil,
    buscar_por_matricula,
    criar_usuario,
    excluir_usuario,
    listar_perfis,
    listar_usuarios,
    resetar_senha,
)

users_bp = Blueprint("users", __name__, url_prefix="/api/v1/users")


def _dal():
    return g.dal


def _erp_dal():
    return get_erp_dal_instance()


def _status_erp_error(codigo: str) -> int:
    if codigo == "nao_encontrado_erp":
        return 404
    if codigo == "erp_indisponivel":
        return 503
    return 400


@users_bp.get("")
@require_config_access
def list_users():
    usuarios = listar_usuarios(_dal())
    return jsonify({"ok": True, "usuarios": usuarios}), 200


@users_bp.get("/perfis")
@require_config_access
def list_profiles():
    return jsonify({"ok": True, "perfis": listar_perfis(_dal())}), 200


@users_bp.get("/erp-funcionario/<matricula>")
@require_config_access
def get_erp_funcionario(matricula: str):
    """Valida matrícula no ERP Oracle e retorna nome/foto do funcionário."""
    resultado = consultar_funcionario_erp(_erp_dal(), matricula)
    if isinstance(resultado, ErpError):
        return json_error(
            resultado.mensagem,
            _status_erp_error(resultado.codigo),
            resultado.codigo,
        )
    return jsonify({"ok": True, "funcionario": resultado}), 200


@users_bp.get("/by-matricula/<matricula>")
@require_config_access
def get_user_by_matricula(matricula: str):
    resultado = buscar_por_matricula(_dal(), matricula, erp_dal=_erp_dal())
    if isinstance(resultado, ServiceError):
        status = 404
        if resultado.codigo == "usuario_inativo":
            status = 409
        elif resultado.codigo == "erp_indisponivel":
            status = 503
        elif resultado.codigo not in ("nao_encontrado", "nao_encontrado_erp"):
            status = 400
        return json_error(resultado.mensagem, status, resultado.codigo)
    return jsonify({"ok": True, "usuario": resultado}), 200


@users_bp.post("")
@require_config_access
def create_user():
    body = request.get_json(silent=True) or {}
    matricula = str(body.get("matricula", ""))
    nome = str(body.get("nome", ""))
    codigo_perfil = int(body.get("codigo_perfil", 0))

    resultado = criar_usuario(
        _dal(),
        matricula,
        nome,
        codigo_perfil,
        id_empresa=body.get("id_empresa"),
        id_turno=body.get("id_turno"),
        id_local=body.get("id_local"),
        erp_dal=_erp_dal(),
    )
    if isinstance(resultado, ServiceError):
        status = 409 if resultado.codigo == "matricula_duplicada" else 400
        if resultado.codigo == "erp_indisponivel":
            status = 503
        elif resultado.codigo == "nao_encontrado_erp":
            status = 404
        return json_error(resultado.mensagem, status, resultado.codigo)
    return jsonify(
        {
            "ok": True,
            "usuario": resultado,
            "mensagem": "Usuário cadastrado com sucesso.",
        }
    ), 201


@users_bp.put("/<int:id_usuario>")
@require_config_access
def update_user_profile(id_usuario: int):
    body = request.get_json(silent=True) or {}
    codigo_perfil = int(body.get("codigo_perfil", 0))
    nome = body.get("nome")
    nome_str = str(nome).strip() if nome is not None else None
    resultado = atualizar_perfil(
        _dal(),
        id_usuario,
        codigo_perfil,
        nome=nome_str,
        id_empresa=body.get("id_empresa"),
        id_turno=body.get("id_turno"),
        id_local=body.get("id_local"),
    )
    if isinstance(resultado, ServiceError):
        status = 404 if resultado.codigo == "nao_encontrado" else 400
        if resultado.codigo == "usuario_inativo":
            status = 409
        return json_error(resultado.mensagem, status, resultado.codigo)
    return jsonify(
        {
            "ok": True,
            "usuario": resultado,
            "mensagem": "Usuário atualizado com sucesso.",
        }
    ), 200


@users_bp.delete("/<int:id_usuario>")
@require_config_access
def delete_user(id_usuario: int):
    erro = excluir_usuario(_dal(), id_usuario)
    if erro:
        status = 404
        if erro.codigo == "usuario_inativo":
            status = 409
        return json_error(erro.mensagem, status, erro.codigo)
    return jsonify({"ok": True, "mensagem": "Usuário excluído com sucesso."}), 200


@users_bp.post("/<int:id_usuario>/reset-password")
@require_admin
def reset_user_password(id_usuario: int):
    resultado = resetar_senha(_dal(), id_usuario)
    if isinstance(resultado, ServiceError):
        status = 404 if resultado.codigo == "nao_encontrado" else 400
        if resultado.codigo == "usuario_inativo":
            status = 409
        return json_error(resultado.mensagem, status, resultado.codigo)
    return jsonify(
        {
            "ok": True,
            "usuario": resultado,
            "mensagem": resultado.get(
                "mensagem", "Reset de usuário realizado com sucesso!"
            ),
        }
    ), 200

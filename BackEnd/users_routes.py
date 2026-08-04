# ----------------------------
# Deus seja Louvado!
# ----------------------------

"""Endpoints REST de usuários — /api/v1/users/* (RF-RN-013..015)."""

from __future__ import annotations

from flask import Blueprint, g, jsonify, request

from .auth_middleware import json_error, require_admin
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


@users_bp.get("")
@require_admin
def list_users():
    usuarios = listar_usuarios(_dal())
    return jsonify({"ok": True, "usuarios": usuarios}), 200


@users_bp.get("/perfis")
@require_admin
def list_profiles():
    return jsonify({"ok": True, "perfis": listar_perfis(_dal())}), 200


@users_bp.get("/by-matricula/<matricula>")
@require_admin
def get_user_by_matricula(matricula: str):
    resultado = buscar_por_matricula(_dal(), matricula)
    if isinstance(resultado, ServiceError):
        status = 404 if resultado.codigo == "nao_encontrado" else 400
        return json_error(resultado.mensagem, status, resultado.codigo)
    return jsonify({"ok": True, "usuario": resultado}), 200


@users_bp.post("")
@require_admin
def create_user():
    body = request.get_json(silent=True) or {}
    matricula = str(body.get("matricula", ""))
    nome = str(body.get("nome", ""))
    codigo_perfil = int(body.get("codigo_perfil", 0))

    resultado = criar_usuario(_dal(), matricula, nome, codigo_perfil)
    if isinstance(resultado, ServiceError):
        status = 409 if resultado.codigo == "matricula_duplicada" else 400
        return json_error(resultado.mensagem, status, resultado.codigo)
    return jsonify(
        {
            "ok": True,
            "usuario": resultado,
            "mensagem": "Usuário cadastrado com sucesso.",
        }
    ), 201


@users_bp.put("/<int:id_usuario>")
@require_admin
def update_user_profile(id_usuario: int):
    body = request.get_json(silent=True) or {}
    codigo_perfil = int(body.get("codigo_perfil", 0))
    nome = body.get("nome")
    nome_str = str(nome).strip() if nome is not None else None
    resultado = atualizar_perfil(_dal(), id_usuario, codigo_perfil, nome=nome_str)
    if isinstance(resultado, ServiceError):
        status = 404 if resultado.codigo == "nao_encontrado" else 400
        return json_error(resultado.mensagem, status, resultado.codigo)
    return jsonify(
        {
            "ok": True,
            "usuario": resultado,
            "mensagem": "Usuário atualizado com sucesso.",
        }
    ), 200


@users_bp.delete("/<int:id_usuario>")
@require_admin
def delete_user(id_usuario: int):
    erro = excluir_usuario(_dal(), id_usuario)
    if erro:
        status = 409 if erro.codigo == "usuario_em_uso" else 404
        return json_error(erro.mensagem, status, erro.codigo)
    return jsonify({"ok": True, "mensagem": "Usuário excluído com sucesso."}), 200


@users_bp.post("/<int:id_usuario>/reset-password")
@require_admin
def reset_user_password(id_usuario: int):
    resultado = resetar_senha(_dal(), id_usuario)
    if isinstance(resultado, ServiceError):
        return json_error(resultado.mensagem, 404, resultado.codigo)
    return jsonify(
        {
            "ok": True,
            "usuario": resultado,
            "mensagem": resultado.get(
                "mensagem", "Reset de usuário realizado com sucesso!"
            ),
        }
    ), 200

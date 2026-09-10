# ----------------------------
# Deus seja Louvado!
# ----------------------------

"""Endpoints REST de usuários — /api/v1/users/* (RF-RN-013..015)."""

from __future__ import annotations

import logging

from flask import Blueprint, g, jsonify, request

from .auth_middleware import json_error, require_admin, require_config_access
from .erp_funcionario_service import (
    MSG_ERP_INDISPONIVEL,
    ERPFuncionarioService,
    ErpError,
    build_erp_funcionario_service,
)
from .erp_service import consultar_funcionario_erp
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
logger = logging.getLogger(__name__)


def _dal():
    return g.dal


def _erp_service_or_error() -> ERPFuncionarioService | ErpError | None:
    """Retorna provider ERP configurado explicitamente ou compat legado."""
    try:
        return build_erp_funcionario_service()
    except Exception as exc:
        logger.error(
            "ERP indisponível ao inicializar provider de funcionários: %s",
            exc,
            exc_info=True,
        )
        return ErpError(MSG_ERP_INDISPONIVEL, "erp_indisponivel")


def _status_erp_error(codigo: str) -> int:
    if codigo in (
        "nao_encontrado_erp",
        "nao_encontrado_rh",
        "funcionario_nao_encontrado",
    ):
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
    erp_service = _erp_service_or_error()
    if erp_service is None:
        return json_error(
            MSG_ERP_INDISPONIVEL,
            503,
            "erp_indisponivel",
        )
    if isinstance(erp_service, ErpError):
        return json_error(
            erp_service.mensagem,
            _status_erp_error(erp_service.codigo),
            erp_service.codigo,
        )

    resultado = consultar_funcionario_erp(erp_service, matricula)
    if isinstance(resultado, ErpError):
        return json_error(
            resultado.mensagem,
            _status_erp_error(resultado.codigo),
            resultado.codigo,
        )
    return jsonify(resultado), 200


@users_bp.get("/by-matricula/<matricula>")
@require_config_access
def get_user_by_matricula(matricula: str):
    erp_service = _erp_service_or_error()
    if erp_service is None:
        return json_error(
            MSG_ERP_INDISPONIVEL,
            503,
            "erp_indisponivel",
        )
    if isinstance(erp_service, ErpError):
        return json_error(
            erp_service.mensagem,
            _status_erp_error(erp_service.codigo),
            erp_service.codigo,
        )

    resultado = buscar_por_matricula(_dal(), matricula, erp_service=erp_service)
    if isinstance(resultado, ServiceError):
        status = 404
        if resultado.codigo == "usuario_inativo":
            status = 409
        elif resultado.codigo == "erp_indisponivel":
            status = 503
        elif resultado.codigo not in (
            "nao_encontrado",
            "nao_encontrado_erp",
            "nao_encontrado_rh",
            "funcionario_nao_encontrado",
        ):
            status = 400
        return json_error(resultado.mensagem, status, resultado.codigo)
    return jsonify({"ok": True, **resultado}), 200


@users_bp.post("")
@require_config_access
def create_user():
    body = request.get_json(silent=True) or {}
    matricula = str(body.get("matricula", ""))
    nome = str(body.get("nome", ""))
    codigo_perfil = int(body.get("codigo_perfil", 0))

    erp_service = _erp_service_or_error()
    if isinstance(erp_service, ErpError):
        return json_error(
            erp_service.mensagem,
            _status_erp_error(erp_service.codigo),
            erp_service.codigo,
        )

    resultado = criar_usuario(
        _dal(),
        matricula,
        nome,
        codigo_perfil,
        id_empresa=body.get("id_empresa"),
        id_turno=body.get("id_turno"),
        id_local=body.get("id_local"),
        erp_service=erp_service,
    )
    if isinstance(resultado, ServiceError):
        status = 409 if resultado.codigo == "matricula_duplicada" else 400
        if resultado.codigo == "erp_indisponivel":
            status = 503
        elif resultado.codigo in ("nao_encontrado_erp", "funcionario_nao_encontrado"):
            status = 404
        elif resultado.codigo == "persistencia":
            status = 500
        return json_error(resultado.mensagem, status, resultado.codigo)

    reativado = bool(resultado.pop("reativado", False))
    senha_tmp = resultado.get("senha_temporaria")
    if reativado:
        return jsonify(
            {
                "ok": True,
                "reativado": True,
                "senha_temporaria": senha_tmp,
                "usuario": resultado,
                "mensagem": "Usuário reativado com sucesso.",
            }
        ), 200

    return jsonify(
        {
            "ok": True,
            "reativado": False,
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
        if erro.codigo == "nao_encontrado":
            status = 404
        elif erro.codigo == "usuario_inativo":
            status = 409
        elif erro.codigo == "persistencia":
            status = 500
        else:
            status = 400
        return json_error(erro.mensagem, status, erro.codigo)
    return jsonify({"ok": True, "mensagem": "Usuário excluído com sucesso."}), 200


@users_bp.post("/<int:id_usuario>/reset-password")
@require_admin
def reset_user_password(id_usuario: int):
    resultado = resetar_senha(_dal(), id_usuario)
    if isinstance(resultado, ServiceError):
        if resultado.codigo == "nao_encontrado":
            status = 404
        elif resultado.codigo == "usuario_inativo":
            status = 409
        elif resultado.codigo == "persistencia":
            status = 500
        else:
            status = 400
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

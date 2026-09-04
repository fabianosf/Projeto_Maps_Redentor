# ----------------------------
# Deus seja Louvado!
# ----------------------------

"""Endpoints de parâmetros da aplicação — /api/v1/config/*"""

from __future__ import annotations

from flask import Blueprint, g, jsonify, request

from .auth_middleware import json_error, require_config_access
from .config_service import (
    obter_config_login,
    obter_qtd_tentativas,
    salvar_config_login,
    salvar_qtd_tentativas,
    ServiceError,
)

config_bp = Blueprint("config", __name__, url_prefix="/api/v1/config")


@config_bp.get("/qtd-tentativas")
@require_config_access
def get_qtd_tentativas():
    cfg = obter_config_login(g.dal)
    return jsonify(
        {
            "ok": True,
            "chave": "QTD_MAX_TENTATIVAS",
            "valor": cfg["qtd_max_tentativas"],
            "bloqueio_tentativas": cfg["bloqueio_tentativas"],
        }
    ), 200


@config_bp.put("/qtd-tentativas")
@require_config_access
def put_qtd_tentativas():
    body = request.get_json(silent=True) or {}
    valor = str(body.get("valor", "")).strip()
    bloqueio = body.get("bloqueio_tentativas", True)
    bloqueio_ativo = bool(bloqueio) if isinstance(bloqueio, bool) else str(bloqueio).strip() in ("1", "true", "True")
    resultado = salvar_config_login(g.dal, valor, bloqueio_ativo)
    if isinstance(resultado, ServiceError):
        return json_error(resultado.mensagem, 400, resultado.codigo)
    return jsonify(
        {
            "ok": True,
            "chave": "QTD_MAX_TENTATIVAS",
            "valor": resultado["qtd_max_tentativas"],
            "bloqueio_tentativas": resultado["bloqueio_tentativas"],
            "mensagem": "Configurações de login atualizadas.",
        }
    ), 200

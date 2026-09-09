# ----------------------------
# Deus seja Louvado!
# ----------------------------

"""Consulta operacional — banco de horas do motorista."""

from __future__ import annotations

from datetime import datetime

from flask import Blueprint, g, jsonify, request

from .auth_middleware import json_error, require_banco_horas_access
from .mapa_service import MapaError, obter_banco_horas_motorista

motoristas_bp = Blueprint("motoristas", __name__, url_prefix="/api/v1/motoristas")


def _dal():
    return g.dal


@motoristas_bp.get("/<int:id_motorista>/banco-horas")
@require_banco_horas_access
def banco_horas_motorista(id_motorista: int):
    data_raw = (request.args.get("data") or "").strip()
    if not data_raw:
        return json_error("Informe data=YYYY-MM-DD.", 400, "validacao")
    try:
        data_ref = datetime.strptime(data_raw[:10], "%Y-%m-%d").date()
    except ValueError:
        return json_error("Data inválida. Use YYYY-MM-DD.", 400, "validacao")

    resultado = obter_banco_horas_motorista(_dal(), id_motorista, data_ref)
    if isinstance(resultado, MapaError):
        status = 404 if resultado.codigo == "nao_encontrado" else 400
        return json_error(resultado.mensagem, status, resultado.codigo)
    return jsonify({"ok": True, "banco_horas": resultado}), 200

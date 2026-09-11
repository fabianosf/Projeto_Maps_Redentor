# ----------------------------
# Deus seja Louvado!
# ----------------------------

"""Consulta operacional — banco de horas do motorista."""

from __future__ import annotations

from datetime import datetime

from flask import Blueprint, g, jsonify, request

from .auth_middleware import json_error, require_banco_horas_access
from .mapa_service import (
    MapaError,
    listar_banco_horas_periodo,
    obter_banco_horas_motorista,
)

motoristas_bp = Blueprint("motoristas", __name__, url_prefix="/api/v1/motoristas")


def _dal():
    return g.dal


def _parse_date_arg(raw: str, label: str):
    texto = (raw or "").strip()
    if not texto:
        return None
    try:
        return datetime.strptime(texto[:10], "%Y-%m-%d").date()
    except ValueError:
        return MapaError(f"{label} inválida. Use YYYY-MM-DD.", "validacao")


def _parse_int_arg(raw: str | None):
    if raw is None or str(raw).strip() == "":
        return None
    try:
        return int(raw)
    except (TypeError, ValueError):
        return MapaError("Filtro numérico inválido.", "validacao")


@motoristas_bp.get("/<int:id_motorista>/banco-horas")
@require_banco_horas_access
def banco_horas_motorista(id_motorista: int):
    data_raw = (request.args.get("data") or "").strip()
    data_ini_raw = (request.args.get("data_ini") or "").strip()
    data_fim_raw = (request.args.get("data_fim") or "").strip()

    id_empresa = _parse_int_arg(request.args.get("id_empresa"))
    if isinstance(id_empresa, MapaError):
        return json_error(id_empresa.mensagem, 400, id_empresa.codigo)
    id_linha = _parse_int_arg(request.args.get("id_linha"))
    if isinstance(id_linha, MapaError):
        return json_error(id_linha.mensagem, 400, id_linha.codigo)
    situacao = (request.args.get("situacao") or "").strip() or None

    # Histórico por período
    if data_ini_raw or data_fim_raw:
        data_ini = _parse_date_arg(data_ini_raw or data_raw, "Data início")
        data_fim = _parse_date_arg(data_fim_raw or data_ini_raw or data_raw, "Data fim")
        if isinstance(data_ini, MapaError):
            return json_error(data_ini.mensagem, 400, data_ini.codigo)
        if isinstance(data_fim, MapaError):
            return json_error(data_fim.mensagem, 400, data_fim.codigo)
        if data_ini is None or data_fim is None:
            return json_error(
                "Informe data_ini e data_fim (YYYY-MM-DD).",
                400,
                "validacao",
            )
        resultado = listar_banco_horas_periodo(
            _dal(),
            id_motorista,
            data_ini,
            data_fim,
            id_empresa=id_empresa,
            id_linha=id_linha,
            situacao=situacao,
        )
        if isinstance(resultado, MapaError):
            status = 404 if resultado.codigo == "nao_encontrado" else 400
            return json_error(resultado.mensagem, status, resultado.codigo)
        return jsonify({"ok": True, "banco_horas_periodo": resultado}), 200

    if not data_raw:
        return json_error(
            "Informe data=YYYY-MM-DD ou data_ini/data_fim.",
            400,
            "validacao",
        )
    data_ref = _parse_date_arg(data_raw, "Data")
    if isinstance(data_ref, MapaError):
        return json_error(data_ref.mensagem, 400, data_ref.codigo)
    assert data_ref is not None

    resultado = obter_banco_horas_motorista(
        _dal(),
        id_motorista,
        data_ref,
        id_empresa=id_empresa,
        id_linha=id_linha,
        situacao=situacao,
    )
    if isinstance(resultado, MapaError):
        status = 404 if resultado.codigo == "nao_encontrado" else 400
        return json_error(resultado.mensagem, status, resultado.codigo)
    return jsonify({"ok": True, "banco_horas": resultado}), 200

# ----------------------------
# Deus seja Louvado!
# ----------------------------

"""Endpoints REST do módulo MAPA — /api/v1/mapas/* (RF-MAP-RN)."""

from __future__ import annotations

import logging
import traceback

from flask import Blueprint, g, jsonify, request

from .auth_middleware import json_error, require_banco_horas_access, require_mapa_access
from .auth_service import UsuarioAuth
from .mapa_service import (
    MapaError,
    atualizar_item_map,
    atualizar_mapa,
    atualizar_viagem,
    criar_item_map,
    criar_mapa,
    criar_viagem,
    dar_baixa_item_map,
    excluir_item_map,
    excluir_mapa,
    excluir_todos_mapas,
    excluir_viagem,
    listar_mapas,
    listar_ocupacao_escalas,
    obter_banco_horas_motorista,
    obter_indicadores,
    obter_mapa_completo,
)

logger = logging.getLogger(__name__)

try:
    from pymysql.err import OperationalError as PyMySQLOperationalError
except ImportError:  # pragma: no cover
    PyMySQLOperationalError = ()  # type: ignore[misc, assignment]

mapa_bp = Blueprint("mapa", __name__, url_prefix="/api/v1/mapas")


def _dal():
    return g.dal


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
    data = request.args.get("data")
    resultado = listar_mapas(_dal(), data)
    if isinstance(resultado, MapaError):
        return json_error(resultado.mensagem, 400, resultado.codigo)
    return jsonify({"ok": True, "mapas": resultado}), 200


@mapa_bp.delete("")
@require_mapa_access
def delete_all_maps():
    """DELETE /api/v1/mapas — remove todos os MAPAs e dependências."""
    resultado = excluir_todos_mapas(_dal())
    if isinstance(resultado, MapaError):
        status = 404 if resultado.codigo == "nao_encontrado" else 400
        return json_error(resultado.mensagem, status, resultado.codigo)
    return jsonify({"ok": True, "excluidos": int(resultado.get("excluidos") or 0)}), 200


@mapa_bp.get("/ocupacao")
@require_mapa_access
def ocupacao_escalas():
    """
    GET /api/v1/mapas/ocupacao
    Veículos e motoristas em escalas EM_ANDAMENTO.
    Query opcional: id_mapa, id_empresa, id_linha, data.
    """
    filtros: dict = {}
    for key in ("id_mapa", "id_empresa", "id_linha"):
        raw = request.args.get(key)
        if raw not in (None, ""):
            try:
                filtros[key] = int(raw)
            except (TypeError, ValueError):
                return json_error(f"{key} inválido.", 400, "validacao")
    data_raw = request.args.get("data")
    if data_raw not in (None, ""):
        filtros["data"] = data_raw

    try:
        resultado = listar_ocupacao_escalas(_dal(), filtros)
    except Exception as exc:  # noqa: BLE001 — falha de SQL/DAL nunca vira 200
        if PyMySQLOperationalError and isinstance(exc, PyMySQLOperationalError):
            is_sql_fail = True
        else:
            # pymysql / driver wrapping / coluna ausente / conexão
            name = type(exc).__name__
            msg = str(exc).lower()
            is_sql_fail = (
                name in ("OperationalError", "ProgrammingError", "DatabaseError", "InterfaceError")
                or "unknown column" in msg
                or "operationalerror" in msg
            )
        if not is_sql_fail:
            raise
        logger.error(
            "Falha SQL em GET /api/v1/mapas/ocupacao: %s\n%s",
            exc,
            traceback.format_exc(),
        )
        return (
            jsonify(
                {
                    "message": "Não foi possível consultar a disponibilidade operacional.",
                    "ok": False,
                    "mensagem": "Não foi possível consultar a disponibilidade operacional.",
                    "codigo": "disponibilidade_indisponivel",
                }
            ),
            500,
        )

    return jsonify(
        {
            "ok": True,
            "veiculos_ocupados": resultado.get("veiculos_ocupados", []),
            "motoristas_ocupados": resultado.get("motoristas_ocupados", []),
            # aliases legados
            "veiculos": resultado.get("veiculos_ocupados", []),
            "motoristas": resultado.get("motoristas_ocupados", []),
        }
    ), 200


@mapa_bp.get("/<int:id_registro>")
@require_mapa_access
def get_map(id_registro: int):
    try:
        resultado = obter_mapa_completo(_dal(), id_registro)
    except Exception as exc:  # noqa: BLE001 — detalhe nunca vira 500 opaco
        logger.error(
            "Falha em GET /api/v1/mapas/%s: %s\n%s",
            id_registro,
            exc,
            traceback.format_exc(),
        )
        return json_error(
            "Não foi possível carregar o detalhe do MAPA. Tente novamente.",
            500,
            "mapa_detalhe_indisponivel",
        )
    if isinstance(resultado, MapaError):
        status = 404 if resultado.codigo == "nao_encontrado" else 400
        return json_error(resultado.mensagem, status, resultado.codigo)
    try:
        return jsonify({"ok": True, "mapa": resultado}), 200
    except TypeError as exc:
        logger.error(
            "Serialização JSON falhou em GET /api/v1/mapas/%s: %s\n%s",
            id_registro,
            exc,
            traceback.format_exc(),
        )
        return json_error(
            "Não foi possível carregar o detalhe do MAPA. Tente novamente.",
            500,
            "mapa_detalhe_indisponivel",
        )


@mapa_bp.post("")
@require_mapa_access
def create_map():
    usuario: UsuarioAuth = g.auth_usuario
    body = request.get_json(silent=True) or {}
    resultado = criar_mapa(_dal(), usuario.id_usuario, body)
    if isinstance(resultado, MapaError):
        status = 400
        if resultado.codigo in (
            "cod_map_esgotado",
            "cod_map_conflito",
            "prefixo_mapa_ausente",
        ):
            status = 409
        elif resultado.codigo in ("empresa_obrigatoria", "empresa_invalida"):
            status = 400
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


def _status_mapa_error(erro: MapaError) -> int:
    if erro.codigo in ("nao_encontrado", "nao_encontrada"):
        return 404
    if erro.codigo == "horario_invalido":
        return 422
    if erro.codigo in (
        "conflito_veiculo",
        "conflito_motorista",
        "conflito_baixa",
        "conflito_sobreposicao",
        "conflito_horario",
        "escala_encerrada",
        "cod_map_esgotado",
        "cod_map_conflito",
    ):
        return 409
    return 400


@mapa_bp.post("/<int:id_registro>/itens")
@require_mapa_access
def create_item(id_registro: int):
    body = request.get_json(silent=True) or {}
    resultado = criar_item_map(_dal(), id_registro, body)
    if isinstance(resultado, MapaError):
        return json_error(
            resultado.mensagem, _status_mapa_error(resultado), resultado.codigo
        )
    return jsonify({"ok": True, "item": resultado}), 201


@mapa_bp.put("/itens/<int:id_item>")
@require_mapa_access
def update_item(id_item: int):
    body = request.get_json(silent=True) or {}
    resultado = atualizar_item_map(_dal(), id_item, body)
    if isinstance(resultado, MapaError):
        return json_error(
            resultado.mensagem, _status_mapa_error(resultado), resultado.codigo
        )
    return jsonify({"ok": True, "item": resultado}), 200


@mapa_bp.post("/itens/<int:id_item>/baixa")
@require_mapa_access
def baixa_item(id_item: int):
    body = request.get_json(silent=True) or {}
    resultado = dar_baixa_item_map(_dal(), id_item, body)
    if isinstance(resultado, MapaError):
        return json_error(
            resultado.mensagem, _status_mapa_error(resultado), resultado.codigo
        )
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
        return json_error(
            resultado.mensagem, _status_mapa_error(resultado), resultado.codigo
        )
    return jsonify({"ok": True, "viagem": resultado}), 201


@mapa_bp.put("/viagens/<int:id_viagem>")
@require_mapa_access
def update_trip(id_viagem: int):
    body = request.get_json(silent=True) or {}
    resultado = atualizar_viagem(_dal(), id_viagem, body)
    if isinstance(resultado, MapaError):
        return json_error(
            resultado.mensagem, _status_mapa_error(resultado), resultado.codigo
        )
    return jsonify({"ok": True, "viagem": resultado}), 200


@mapa_bp.delete("/viagens/<int:id_viagem>")
@require_mapa_access
def delete_trip(id_viagem: int):
    erro = excluir_viagem(_dal(), id_viagem)
    if erro:
        return json_error(erro.mensagem, 404, erro.codigo)
    return jsonify({"ok": True}), 200

# ----------------------------
# Deus seja Louvado!
# ----------------------------

"""Endpoints REST — /api/v1/guia/* (Tela 08)."""

from __future__ import annotations

from flask import Blueprint, g, jsonify, request

from .auth_middleware import json_error, require_session
from .constants import PERFIS_MAPA
from .guia_consolidacao import consultar_guia_consolidada, registrar_ajuste_manual
from .guia_escala_service import (
    listar_escalas_guia,
    obter_contexto_escala,
    registrar_alteracao_escala,
)
from .guia_roleta_service import (
    historico_leitura,
    salvar_leitura_roleta,
    sugerir_leitura_inicial,
)
from .guia_service import (
    GuiaError,
    atualizar_guia,
    buscar_por_numero,
    criar_guia,
    excluir_guia,
)

guia_bp = Blueprint("guia", __name__, url_prefix="/api/v1/guia")


def _parse_bool(valor: str | None) -> bool:
    if valor is None:
        return False
    return str(valor).strip().lower() in {"1", "true", "sim", "yes", "on"}


def _parse_int_arg(nome: str):
    raw = request.args.get(nome)
    if raw is None or str(raw).strip() == "":
        return None
    try:
        return int(raw)
    except (TypeError, ValueError):
        return GuiaError(f"Filtro {nome} inválido.", "validacao")


def _resposta_consulta():
    """GET consolidado — Mapa + Viagens + Roleta."""
    id_turno = _parse_int_arg("id_turno")
    if isinstance(id_turno, GuiaError):
        return json_error(id_turno.mensagem, 400, id_turno.codigo)
    id_linha = _parse_int_arg("id_linha")
    if isinstance(id_linha, GuiaError):
        return json_error(id_linha.mensagem, 400, id_linha.codigo)

    resultado = consultar_guia_consolidada(
        g.dal,
        request.args.get("data"),
        sentido=request.args.get("sentido"),
        origem=request.args.get("origem"),
        status=request.args.get("status"),
        id_turno=id_turno,
        id_linha=id_linha,
        somente_pendencias=_parse_bool(request.args.get("pendencias")),
    )
    if isinstance(resultado, GuiaError):
        return json_error(resultado.mensagem, 400, resultado.codigo)
    return jsonify({"ok": True, **resultado}), 200


@guia_bp.get("/consulta")
@require_session
def consulta_guias():
    """GET /api/v1/guia/consulta?data=dd/mm/aaaa — visão consolidada (leitura)."""
    return _resposta_consulta()


@guia_bp.get("/escalas")
@require_session
def listar_escalas():
    """
    GET /api/v1/guia/escalas?data=dd/mm/aaaa&id_mapa=
    Mapas/escalas do dia para preencher a Nova Guia.
    """
    id_mapa = _parse_int_arg("id_mapa")
    if isinstance(id_mapa, GuiaError):
        return json_error(id_mapa.mensagem, 400, id_mapa.codigo)
    resultado = listar_escalas_guia(g.dal, request.args.get("data") or "", id_mapa)
    if isinstance(resultado, GuiaError):
        return json_error(resultado.mensagem, 400, resultado.codigo)
    return jsonify({"ok": True, **resultado}), 200


@guia_bp.get("/contexto-escala")
@require_session
def contexto_escala():
    """GET /api/v1/guia/contexto-escala?id_item= — dados readonly da escala."""
    id_item = _parse_int_arg("id_item")
    if isinstance(id_item, GuiaError):
        return json_error(id_item.mensagem, 400, id_item.codigo)
    if not id_item:
        return json_error("Informe id_item.", 400, "validacao")
    resultado = obter_contexto_escala(g.dal, id_item)
    if isinstance(resultado, GuiaError):
        status = 404 if resultado.codigo == "nao_encontrado" else 400
        return json_error(resultado.mensagem, status, resultado.codigo)
    return jsonify({"ok": True, "contexto": resultado}), 200


@guia_bp.post("/escala/<int:id_item>/alteracao")
@require_session
def alteracao_escala(id_item: int):
    """
    POST /api/v1/guia/escala/<id_item>/alteracao
    Troca veículo/motorista/horário com justificativa e auditoria (Admin/Despachante).
    """
    if g.auth_usuario.codigo_perfil not in PERFIS_MAPA:
        return json_error(
            "Sem permissão para alterar escala.", 403, "sem_permissao"
        )
    body = request.get_json(silent=True) or {}
    resultado = registrar_alteracao_escala(
        g.dal, id_item, body, int(g.auth_usuario.id_usuario)
    )
    if isinstance(resultado, GuiaError):
        status = 404 if resultado.codigo == "nao_encontrado" else 400
        return json_error(resultado.mensagem, status, resultado.codigo)
    return jsonify(
        {
            "ok": True,
            "contexto": resultado,
            "mensagem": "Alteração de escala registrada com auditoria.",
        }
    ), 200


@guia_bp.route("", methods=["GET", "POST"])
@guia_bp.route("/", methods=["GET", "POST"])
@require_session
def guia_collection():
    """
    GET  /api/v1/guia?data=&sentido=&origem=&status=&pendencias=
         — consolidado (mesmo contrato de /consulta)
    POST /api/v1/guia — criar guia (fluxo atual)
    """
    if request.method == "GET":
        return _resposta_consulta()

    body = request.get_json(silent=True) or {}
    resultado = criar_guia(g.dal, body)
    if isinstance(resultado, GuiaError):
        status = 409 if resultado.codigo == "numero_duplicado" else 400
        return json_error("Não foi possível cadastrar a guia!", status, resultado.codigo)
    return jsonify(
        {"ok": True, "guia": resultado, "mensagem": "Guia cadastrada com sucesso!"}
    ), 201


@guia_bp.post("/<int:id_guia>/ajuste-manual")
@require_session
def ajuste_manual(id_guia: int):
    """Ajuste manual com justificativa — não sobrescreve roleta original."""
    body = request.get_json(silent=True) or {}
    resultado = registrar_ajuste_manual(
        g.dal,
        id_guia,
        sentido=str(body.get("sentido", "")),
        embarques=body.get("embarques"),
        justificativa=str(body.get("justificativa", "")),
    )
    if isinstance(resultado, GuiaError):
        status = 404 if resultado.codigo == "nao_encontrado" else 400
        return json_error(resultado.mensagem, status, resultado.codigo)
    return jsonify(
        {
            "ok": True,
            "guia": resultado,
            "mensagem": "Ajuste manual registrado com auditoria.",
        }
    ), 200


@guia_bp.post("/roletas")
@require_session
def salvar_roleta():
    """Registra/atualiza leitura Ja E ou RioCard (ini/fim) por viagem."""
    body = request.get_json(silent=True) or {}
    id_usuario = int(g.auth_usuario.id_usuario)
    resultado = salvar_leitura_roleta(g.dal, body, id_usuario)
    if isinstance(resultado, GuiaError):
        status = 404 if resultado.codigo == "nao_encontrado" else 400
        return json_error(resultado.mensagem, status, resultado.codigo)
    return jsonify(
        {
            "ok": True,
            "leitura": resultado,
            "mensagem": "Leitura registrada com sucesso.",
        }
    ), 200


@guia_bp.get("/roletas/sugestao")
@require_session
def sugestao_roleta():
    """Sugere leitura inicial = final da viagem anterior do mesmo veículo."""
    id_veiculo = request.args.get("id_veiculo", type=int)
    fonte = request.args.get("fonte", "")
    sentido = request.args.get("sentido", "")
    if not id_veiculo:
        return json_error("Informe id_veiculo.", 400, "validacao")
    sug = sugerir_leitura_inicial(
        g.dal, id_veiculo=id_veiculo, fonte=fonte, sentido=sentido
    )
    return jsonify({"ok": True, "leitura_ini": sug}), 200


@guia_bp.get("/roletas/<int:id_leitura>/historico")
@require_session
def historico_roleta(id_leitura: int):
    resultado = historico_leitura(g.dal, id_leitura)
    if isinstance(resultado, GuiaError):
        return json_error(resultado.mensagem, 404, resultado.codigo)
    return jsonify({"ok": True, "historico": resultado}), 200


@guia_bp.get("/by-numero/<numero>")
@require_session
def get_by_numero(numero: str):
    resultado = buscar_por_numero(g.dal, numero)
    if isinstance(resultado, GuiaError):
        status = 404 if resultado.codigo == "nao_encontrado" else 400
        return json_error(resultado.mensagem, status, resultado.codigo)
    return jsonify({"ok": True, "guia": resultado}), 200


@guia_bp.put("/<int:id_guia>")
@require_session
def update_guia(id_guia: int):
    body = request.get_json(silent=True) or {}
    resultado = atualizar_guia(g.dal, id_guia, body)
    if isinstance(resultado, GuiaError):
        status = 404 if resultado.codigo == "nao_encontrado" else 400
        if resultado.codigo == "numero_duplicado":
            status = 409
        return json_error(resultado.mensagem, status, resultado.codigo)
    return jsonify({"ok": True, "guia": resultado, "mensagem": "Guia atualizada com sucesso."}), 200


@guia_bp.delete("/<int:id_guia>")
@require_session
def delete_guia(id_guia: int):
    erro = excluir_guia(g.dal, id_guia)
    if erro:
        status = 409 if erro.codigo == "guia_em_uso" else 404
        return json_error(erro.mensagem, status, erro.codigo)
    return jsonify({"ok": True, "mensagem": "Guia excluída com sucesso."}), 200

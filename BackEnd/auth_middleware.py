# ----------------------------
# Deus seja Louvado!
# ----------------------------

"""Middleware de autenticação compartilhado (RF-RN-008, RF-RN-010)."""

from __future__ import annotations

from functools import wraps
from typing import Any, Callable

from flask import Response, g, jsonify, request

from .auth_service import UsuarioAuth, buscar_usuario_por_id
from .auth_session import build_session_clear_cookie, destroy_session, get_current_session
from .constants import PERFIL_ADMIN, PERFIS_CONFIG, PERFIS_MAPA
from .session_store import SessionRecord


def _get_dal():
    dal = getattr(g, "dal", None)
    if dal is None:
        raise RuntimeError("DAL não configurado no contexto Flask")
    return dal


def _apply_cookie(response: Response, cookie: dict[str, Any]) -> Response:
    response.set_cookie(
        cookie["key"],
        cookie["value"],
        max_age=cookie.get("max_age"),
        httponly=cookie.get("httponly", True),
        secure=cookie.get("secure", False),
        samesite=str(cookie.get("samesite", "lax")).capitalize(),
        path=cookie.get("path", "/"),
    )
    return response


def json_error(mensagem: str, status: int, codigo: str = "auth_error"):
    return jsonify({"ok": False, "mensagem": mensagem, "codigo": codigo}), status


def require_session(f: Callable) -> Callable:
    @wraps(f)
    def wrapper(*args, **kwargs):
        session = get_current_session(request.cookies)
        if session is None:
            return json_error("Operação não autorizada.", 401, "sessao_invalida")

        usuario = buscar_usuario_por_id(_get_dal(), session.id_usuario)
        if usuario is None or not usuario.ativo:
            destroy_session(request.cookies)
            response, status = json_error(
                "Operação não autorizada.", 401, "sessao_invalida"
            )
            return _apply_cookie(response, build_session_clear_cookie()), status

        g.auth_session = session
        g.auth_usuario = usuario
        return f(*args, **kwargs)

    return wrapper


def require_admin(f: Callable) -> Callable:
    @wraps(f)
    @require_session
    def wrapper(*args, **kwargs):
        usuario: UsuarioAuth = g.auth_usuario
        if usuario.codigo_perfil != PERFIL_ADMIN:
            return json_error("Operação não autorizada.", 403, "perfil_negado")
        return f(*args, **kwargs)

    return wrapper


def require_config_access(f: Callable) -> Callable:
    """RN-03 — Administrador ou Inspetor (Tela 09 e cadastros associados)."""

    @wraps(f)
    @require_session
    def wrapper(*args, **kwargs):
        usuario: UsuarioAuth = g.auth_usuario
        if usuario.codigo_perfil not in PERFIS_CONFIG:
            return json_error("Operação não autorizada.", 403, "perfil_negado")
        return f(*args, **kwargs)

    return wrapper


def require_mapa_access(f: Callable) -> Callable:
    """RF-MAP — Administrador ou Despachante."""

    @wraps(f)
    @require_session
    def wrapper(*args, **kwargs):
        usuario: UsuarioAuth = g.auth_usuario
        if usuario.codigo_perfil not in PERFIS_MAPA:
            return json_error("Operação não autorizada.", 403, "perfil_negado")
        return f(*args, **kwargs)

    return wrapper


def current_session() -> SessionRecord | None:
    return get_current_session(request.cookies)

# ----------------------------
# Deus seja Louvado!
# ----------------------------

"""
Endpoints REST de autenticação — /api/v1/auth/*

Conforme RF-RN-008, RF-RN-010, RF-RN-011 e RF-RN-012.
"""

from __future__ import annotations

from typing import Any, Callable, Optional

from flask import Blueprint, Response, g, jsonify, request

from .auth_middleware import (
    _apply_cookie,
    json_error,
    require_session,
)
from .auth_service import (
    AuthError,
    DB_UNAVAILABLE_MESSAGE,
    LoginSuccess,
    autenticar_login,
    cancelar_troca_senha,
    trocar_senha,
    usuario_publico,
)
from .auth_session import (
    build_session_clear_cookie,
    build_session_cookie,
    create_authenticated_session,
    destroy_session,
    get_current_session,
)
from .security import limiter
from .session_store import SessionRecord

auth_bp = Blueprint("auth", __name__, url_prefix="/api/v1/auth")


def init_auth_routes(app, dal_factory: Callable[[], Any]) -> None:
    @app.before_request
    def _bind_dal():
        g.dal = dal_factory()


@auth_bp.post("/login")
@limiter.limit("10 per minute")
def login():
    body = request.get_json(silent=True) or {}
    matricula = str(body.get("matricula", "")).strip()
    senha = str(body.get("senha", ""))

    # DAL engole falha de conexão e devolve DataFrame vazio → sem este check
    # o login retornava 401 "Login inválido!" com MariaDB parado.
    if not g.dal.test_connection():
        return json_error(DB_UNAVAILABLE_MESSAGE, 503, "db_indisponivel")

    resultado = autenticar_login(g.dal, matricula, senha)
    if isinstance(resultado, AuthError):
        return json_error(resultado.mensagem, 401, resultado.codigo)

    assert isinstance(resultado, LoginSuccess)
    usuario = resultado.usuario
    payload = {
        "ok": True,
        "trocar_senha": usuario.trocar_senha,
        "usuario": usuario_publico(usuario),
    }

    response = jsonify(payload)

    if usuario.trocar_senha:
        payload["change_token"] = resultado.change_token
        response = jsonify(payload)
        return _apply_cookie(response, build_session_clear_cookie()), 200

    session_id = create_authenticated_session(
        id_usuario=usuario.id_usuario,
        matricula=usuario.matricula,
        codigo_perfil=usuario.codigo_perfil,
        nome=usuario.nome,
    )
    return _apply_cookie(response, build_session_cookie(session_id)), 200


@auth_bp.post("/change-password")
@limiter.limit("10 per minute")
def change_password():
    body = request.get_json(silent=True) or {}
    change_token = str(body.get("change_token", "")).strip()
    nova_senha = str(body.get("nova_senha", ""))
    confirmacao = str(body.get("confirmacao_senha", body.get("confirmacao", "")))

    if not change_token:
        return json_error("Operação não autorizada.", 401, "token_invalido")

    resultado = trocar_senha(g.dal, change_token, nova_senha, confirmacao)
    if isinstance(resultado, AuthError):
        status = 401 if resultado.codigo == "token_invalido" else 400
        return json_error(resultado.mensagem, status, resultado.codigo)

    response = jsonify(resultado)
    return _apply_cookie(response, build_session_clear_cookie()), 200


@auth_bp.post("/cancel-change-password")
@limiter.limit("10 per minute")
def cancel_change_password():
    body = request.get_json(silent=True) or {}
    change_token = body.get("change_token")
    if change_token is not None:
        change_token = str(change_token).strip() or None

    payload = cancelar_troca_senha(change_token)
    response = jsonify(payload)
    return _apply_cookie(response, build_session_clear_cookie()), 200


@auth_bp.post("/cancel-login")
@limiter.limit("10 per minute")
def cancel_login():
    destroy_session(request.cookies)
    response = jsonify({"ok": True})
    return _apply_cookie(response, build_session_clear_cookie()), 200


@auth_bp.post("/logout")
@require_session
def logout():
    destroy_session(request.cookies)
    response = jsonify({"ok": True})
    return _apply_cookie(response, build_session_clear_cookie()), 200


@auth_bp.get("/me")
@require_session
def me():
    session: SessionRecord = g.auth_session
    usuario = g.auth_usuario
    return jsonify(
        {
            "ok": True,
            "usuario": usuario_publico(usuario),
            "sessao": {
                "matricula": session.matricula,
                "codigo_perfil": session.codigo_perfil,
            },
        }
    ), 200


def session_from_request() -> Optional[SessionRecord]:
    """Helper para rotas protegidas fora do blueprint auth."""
    return get_current_session(request.cookies)

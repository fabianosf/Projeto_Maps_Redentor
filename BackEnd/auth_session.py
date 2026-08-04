# ----------------------------
# Deus seja Louvado!
# ----------------------------

"""
Constantes e helpers de sessão HTTP para o RedMapa.

Conforme RF-RN-008, RF-RN-010 e RF-RN-011 em Doc/Requisitos_Ciclo_Login_MAP.md.
"""

from __future__ import annotations

import os
from typing import Any, Mapping, MutableMapping, Optional

from .session_store import SessionRecord, session_store

SESSION_COOKIE_NAME = "redmapa_sid"
SESSION_TTL_SECONDS = 8 * 3600
PASSWORD_CHANGE_TOKEN_TTL_SECONDS = 15 * 60


def cookie_secure() -> bool:
    return os.getenv("REDMAPA_COOKIE_SECURE", "false").lower() in ("1", "true", "yes")


def build_session_cookie(session_id: str) -> dict[str, Any]:
    """Atributos do cookie de sessão (RF-RN-008)."""
    return {
        "key": SESSION_COOKIE_NAME,
        "value": session_id,
        "max_age": SESSION_TTL_SECONDS,
        "httponly": True,
        "secure": cookie_secure(),
        "samesite": "lax",
        "path": "/",
    }


def build_session_clear_cookie() -> dict[str, Any]:
    """Remove o cookie de sessão no logout ou cancelar login."""
    return {
        "key": SESSION_COOKIE_NAME,
        "value": "",
        "max_age": 0,
        "httponly": True,
        "secure": cookie_secure(),
        "samesite": "lax",
        "path": "/",
    }


def read_session_id(cookies: Mapping[str, str]) -> Optional[str]:
    return cookies.get(SESSION_COOKIE_NAME)


def get_current_session(cookies: Mapping[str, str]) -> Optional[SessionRecord]:
    return session_store.get(read_session_id(cookies))


def create_authenticated_session(
    id_usuario: int,
    matricula: str,
    codigo_perfil: int,
    nome: str,
) -> str:
    session_store.destroy_all_for_user(id_usuario)
    return session_store.create(
        id_usuario=id_usuario,
        matricula=matricula,
        codigo_perfil=codigo_perfil,
        nome=nome,
    )


def destroy_session(cookies: Mapping[str, str]) -> bool:
    session_id = read_session_id(cookies)
    return session_store.destroy(session_id)


def apply_set_cookie(headers: MutableMapping[str, str], cookie: dict[str, Any]) -> None:
    """
    Monta header Set-Cookie sem dependência de framework web.
    Uso: apply_set_cookie(response_headers, build_session_cookie(sid))
    """
    parts = [f"{cookie['key']}={cookie['value']}"]
    if cookie.get("max_age") is not None:
        parts.append(f"Max-Age={cookie['max_age']}")
    if cookie.get("path"):
        parts.append(f"Path={cookie['path']}")
    if cookie.get("httponly"):
        parts.append("HttpOnly")
    if cookie.get("secure"):
        parts.append("Secure")
    samesite = cookie.get("samesite")
    if samesite:
        parts.append(f"SameSite={samesite}")

    existing = headers.get("Set-Cookie")
    header_value = "; ".join(parts)
    if existing:
        headers["Set-Cookie"] = f"{existing}, {header_value}"
    else:
        headers["Set-Cookie"] = header_value

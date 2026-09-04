# ----------------------------
# Deus seja Louvado!
# ----------------------------

"""CORS, rate-limit e security headers — configuração central."""

from __future__ import annotations

import os
from typing import Iterable

from flask import Flask, Response
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Limiter compartilhado — rotas de auth aplicam @limiter.limit(...)
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[],
    storage_uri="memory://",
)


def _cors_origins() -> list[str]:
    """
    Origens explícitas (nunca '*').
    REDMAPA_CORS_ORIGINS=http://localhost:5173,https://app.exemplo.com
    """
    raw = os.getenv(
        "REDMAPA_CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173",
    )
    origins = [o.strip() for o in raw.split(",") if o.strip()]
    # Bloqueia wildcard — credentials + cookie exigem origem explícita.
    filtered = [o for o in origins if o != "*"]
    if not filtered:
        filtered = ["http://localhost:5173"]
    return filtered


def init_security(app: Flask) -> None:
    """Aplica CORS, Limiter e headers de segurança."""
    origins = _cors_origins()
    app.config["REDMAPA_CORS_ORIGINS"] = origins

    CORS(
        app,
        resources={r"/api/*": {"origins": origins}},
        supports_credentials=True,
        allow_headers=["Content-Type", "Authorization"],
        methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    )

    # Em testes o rate-limit é desligado para não flaky.
    if app.config.get("TESTING"):
        app.config["RATELIMIT_ENABLED"] = False

    limiter.init_app(app)

    @app.after_request
    def _security_headers(response: Response) -> Response:
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault(
            "Content-Security-Policy",
            "default-src 'none'; frame-ancestors 'none'; base-uri 'none'",
        )
        response.headers.setdefault("Referrer-Policy", "no-referrer")
        response.headers.setdefault(
            "Permissions-Policy",
            "geolocation=(), microphone=(), camera=()",
        )
        return response


def cors_origins() -> Iterable[str]:
    return _cors_origins()

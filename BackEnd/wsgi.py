# ----------------------------
# Deus seja Louvado!
# ----------------------------
"""WSGI entrypoint — produção (Gunicorn/uWSGI). Não use Flask dev server."""

from __future__ import annotations

from BackEnd.app import create_app

app = create_app()

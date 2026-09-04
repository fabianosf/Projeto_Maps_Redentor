# ----------------------------
# Deus seja Louvado!
# ----------------------------

"""Endpoints REST — /api/v1/cadastros (dados mestres operacionais)."""

from __future__ import annotations

from flask import Blueprint, g, jsonify

from .auth_middleware import require_session
from .cadastros_service import listar_cadastros_mestres

cadastros_bp = Blueprint("cadastros", __name__, url_prefix="/api/v1/cadastros")


@cadastros_bp.get("")
@require_session
def cadastros_mestres():
    return jsonify({"ok": True, "cadastros": listar_cadastros_mestres(g.dal)}), 200

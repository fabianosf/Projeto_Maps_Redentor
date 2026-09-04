# ----------------------------
# Deus seja Louvado!
# ----------------------------

"""
Aplicação Flask — RedMapa BackEnd.

Executar:
    python -m BackEnd.app

Variáveis de ambiente:
    REDMAPA_CONFIG        — basename em DAL/arquivos_crip/arq/ (padrão: map)
    REDMAPA_SGBD          — mariadb | postgresql (padrão: mariadb)
    REDMAPA_COOKIE_SECURE — true em produção (HTTPS)
    REDMAPA_CORS_ORIGINS  — origens CORS separadas por vírgula (sem '*')
    REDMAPA_HOST          — padrão 0.0.0.0
    REDMAPA_PORT          — padrão 5000
    FLASK_DEBUG           — 1 para debug
"""

from __future__ import annotations

import os

from flask import Flask, jsonify

from .auth_routes import auth_bp, init_auth_routes
from .dal_factory import get_dal_instance as get_dal
from .security import init_security
from .users_routes import users_bp


def create_app() -> Flask:
    app = Flask(__name__, static_folder=None)
    app.config["JSON_AS_ASCII"] = False

    init_security(app)
    init_auth_routes(app, get_dal)

    app.register_blueprint(auth_bp)
    app.register_blueprint(users_bp)

    from .cadastros_routes import cadastros_bp

    app.register_blueprint(cadastros_bp)

    from .config_routes import config_bp

    app.register_blueprint(config_bp)

    from .indicadores_config_routes import indicadores_config_bp

    app.register_blueprint(indicadores_config_bp)

    from .entrada_saida_routes import entrada_saida_bp

    app.register_blueprint(entrada_saida_bp)

    from .guia_routes import guia_bp

    app.register_blueprint(guia_bp)

    from .mensagem_routes import mensagem_bp

    app.register_blueprint(mensagem_bp)

    from .mapa_routes import mapa_bp

    app.register_blueprint(mapa_bp)

    @app.get("/api/v1/health")
    def health():
        dal = get_dal()
        db_ok = dal.test_connection()
        status = 200 if db_ok else 503
        return jsonify({"ok": db_ok, "servico": "redmapa-api"}), status

    return app


app = create_app()


if __name__ == "__main__":
    host = os.getenv("REDMAPA_HOST", "0.0.0.0")
    port = int(os.getenv("REDMAPA_PORT", "5000"))
    debug = os.getenv("FLASK_DEBUG", "0") in ("1", "true", "yes")
    app.run(host=host, port=port, debug=debug)

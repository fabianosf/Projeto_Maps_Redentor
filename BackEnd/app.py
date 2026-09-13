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
    ERP_PROVIDER          — mock | oracle | disabled
    REDMAPA_ERP_CONFIG    — basename erp.dat (padrão: erp)
    REDMAPA_ERP_SGBD      — oracle (DAL ERP)
    ERP_ORACLE_DSN        — Easy Connect/DSN Oracle opcional (sem erp.dat)
    ERP_ORACLE_HOST       — host Oracle (se DSN não for usado)
    ERP_ORACLE_PORT       — porta Oracle (padrão 1521)
    ERP_ORACLE_SERVICE_NAME — service name Oracle
    ERP_ORACLE_USER       — usuário Oracle/ERP
    ERP_ORACLE_PASSWORD   — senha Oracle/ERP
    ERP_ORACLE_TIMEOUT_MS — timeout de consulta Oracle
    REDMAPA_ERP_ENABLED   — legado 0|1; prefira ERP_PROVIDER
    REDMAPA_ENV           — development | staging | production
    REDMAPA_COOKIE_SECURE — true em produção (HTTPS)
    REDMAPA_COOKIE_SAMESITE — lax | strict | none (none exige Secure)
    REDMAPA_CORS_ORIGINS  — origens CORS separadas por vírgula (sem '*')
    REDMAPA_METRICS_TOKEN — token para GET /api/v1/metrics (produção)
    REDMAPA_HOST          — padrão 0.0.0.0
    REDMAPA_PORT          — padrão 5000
    FLASK_DEBUG           — 1 para debug (proibido em production)
"""

from __future__ import annotations

import logging
import os

from flask import Flask, jsonify

from .auth_routes import auth_bp, init_auth_routes
from .dal_factory import get_dal_instance as get_dal
from .env_loader import load_backend_env
from .observability import ensure_correlation_id, init_observability
from .security import init_security
from .users_routes import users_bp

# Garante ERP_PROVIDER / REDMAPA_* do BackEnd/.env (sem sobrescrever o shell).
load_backend_env()

logger = logging.getLogger("redmapa")


def _assert_runtime_guards() -> None:
    """Bloqueia misconfig crítica — sem fallback silencioso de produção → mock."""
    env = (os.getenv("REDMAPA_ENV") or "development").strip().lower()
    erp = (os.getenv("ERP_PROVIDER") or "").strip().lower()
    debug = os.getenv("FLASK_DEBUG", "0").lower() in ("1", "true", "yes")

    if env == "production":
        if erp == "mock":
            raise RuntimeError(
                "REDMAPA_ENV=production não permite ERP_PROVIDER=mock. "
                "Use ERP_PROVIDER=oracle (sem fallback para mock)."
            )
        if debug:
            raise RuntimeError(
                "REDMAPA_ENV=production não permite FLASK_DEBUG ativo."
            )
        if os.getenv("REDMAPA_COOKIE_SECURE", "false").lower() not in (
            "1",
            "true",
            "yes",
        ):
            logger.warning(
                "Produção sem REDMAPA_COOKIE_SECURE=true — cookies podem "
                "não ser enviados em HTTPS."
            )
    if env in ("staging", "production") and erp == "mock":
        logger.warning(
            "ERP_PROVIDER=mock em %s — apenas homologação controlada com "
            "dados mascarados; produção exige oracle.",
            env,
        )


def create_app() -> Flask:
    _assert_runtime_guards()
    app = Flask(__name__, static_folder=None)
    app.config["JSON_AS_ASCII"] = False
    app.config["PROPAGATE_EXCEPTIONS"] = False

    init_security(app)
    init_observability(app)
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

    from .motoristas_routes import motoristas_bp

    app.register_blueprint(motoristas_bp)

    from .designacao_routes import designacoes_bp

    app.register_blueprint(designacoes_bp)

    @app.get("/api/v1/health")
    def health():
        dal = get_dal()
        db_ok = dal.test_connection()
        env = (os.getenv("REDMAPA_ENV") or "development").strip().lower()
        erp = (os.getenv("ERP_PROVIDER") or "disabled").strip().lower()
        status = 200 if db_ok else 503
        return (
            jsonify(
                {
                    "ok": db_ok,
                    "servico": "redmapa-api",
                    "ambiente": env,
                    "sgbd": (os.getenv("REDMAPA_SGBD") or "mariadb").lower(),
                    "erp_provider": erp,
                    "correlation_id": ensure_correlation_id(),
                }
            ),
            status,
        )

    return app


app = create_app()


if __name__ == "__main__":
    # Dev only. Produção: gunicorn -w 4 -b 127.0.0.1:5000 BackEnd.wsgi:app
    host = os.getenv("REDMAPA_HOST", "0.0.0.0")
    port = int(os.getenv("REDMAPA_PORT", "5000"))
    debug = os.getenv("FLASK_DEBUG", "0") in ("1", "true", "yes")
    if (os.getenv("REDMAPA_ENV") or "").strip().lower() == "production":
        raise SystemExit(
            "Não inicie com python -m BackEnd.app em production. "
            "Use Gunicorn: gunicorn -w 4 -b 127.0.0.1:5000 BackEnd.wsgi:app"
        )
    app.run(host=host, port=port, debug=debug)

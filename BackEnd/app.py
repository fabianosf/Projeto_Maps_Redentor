# ----------------------------

# Deus seja Louvado!

# ----------------------------



"""

Aplicação Flask — RedMapa BackEnd.



Executar:

    python -m BackEnd.app



Variáveis de ambiente:

    REDMAPA_CONFIG       — basename em DAL/arquivos_crip/arq/ (padrão: map_MariaDB)

    REDMAPA_SGBD         — mariadb | postgresql (padrão: mariadb)

    REDMAPA_COOKIE_SECURE — true em produção (HTTPS)

    REDMAPA_HOST         — padrão 0.0.0.0

    REDMAPA_PORT         — padrão 5000

    FLASK_DEBUG          — 1 para debug

"""



from __future__ import annotations



import os

from typing import Optional



from flask import Flask, jsonify



from .auth_routes import auth_bp, init_auth_routes

from .mapa_routes import mapa_bp

from .users_routes import users_bp

from .DAL import DAL



BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ARQUIVOS_CRIP_DIR = os.path.join(BASE_DIR, "DAL", "arquivos_crip")





def _normalizar_config_arquivo(valor: str) -> str:

    nome = (valor or "map_MariaDB").strip()

    if nome.lower().endswith(".dat"):

        nome = nome[:-4]

    return nome





def _create_dal() -> DAL:

    config_arquivo = _normalizar_config_arquivo(os.getenv("REDMAPA_CONFIG", "map_MariaDB"))

    sgbd = os.getenv("REDMAPA_SGBD", "mariadb").strip().lower()

    return DAL(

        config_arquivo=config_arquivo,

        pasta_conf=ARQUIVOS_CRIP_DIR,

        sgbd=sgbd,

    )





_dal_instance: Optional[DAL] = None





def get_dal() -> DAL:

    global _dal_instance

    if _dal_instance is None:

        _dal_instance = _create_dal()

    return _dal_instance





def create_app() -> Flask:

    app = Flask(__name__, static_folder=None)

    app.config["JSON_AS_ASCII"] = False



    init_auth_routes(app, get_dal)

    app.register_blueprint(auth_bp)

    app.register_blueprint(users_bp)

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

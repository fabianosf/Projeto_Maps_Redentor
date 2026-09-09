# ----------------------------
# Deus seja Louvado!
# ----------------------------
"""DAL SQLite in-memory para testes — sem alterar lógica de negócio."""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import date
from typing import Any, Optional

import pandas as pd

from BackEnd.auth_service import hash_senha

SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

CREATE TABLE tb_perfil (
    id_perfil INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo_perfil INTEGER NOT NULL UNIQUE,
    descricao TEXT NOT NULL
);

CREATE TABLE tb_empresa (
    id_empresa INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo_empresa INTEGER NOT NULL UNIQUE,
    descricao TEXT NOT NULL,
    ativo INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE tb_turno (
    id_turno INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo_turno INTEGER NOT NULL UNIQUE,
    descricao TEXT NOT NULL,
    ativo INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE tb_local (
    id_local INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo_local INTEGER NOT NULL UNIQUE,
    descricao TEXT NOT NULL,
    ativo INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE tb_linha (
    id_linha INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo_linha INTEGER NOT NULL UNIQUE,
    id_empresa INTEGER NOT NULL,
    descricao TEXT NOT NULL,
    id_local_origem INTEGER NOT NULL,
    id_local_destino INTEGER NOT NULL,
    ativo INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE tb_veiculo (
    id_veiculo INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo_veiculo INTEGER NOT NULL UNIQUE,
    numero_frota TEXT NOT NULL UNIQUE,
    placa TEXT NOT NULL,
    ativo INTEGER NOT NULL DEFAULT 1,
    id_empresa INTEGER
);

CREATE TABLE tb_motorista (
    id_motorista INTEGER PRIMARY KEY AUTOINCREMENT,
    matricula TEXT NOT NULL UNIQUE,
    nome TEXT NOT NULL,
    ativo INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE tb_usuario (
    id_usuario INTEGER PRIMARY KEY AUTOINCREMENT,
    matricula TEXT NOT NULL UNIQUE,
    nome TEXT NOT NULL,
    senha TEXT NOT NULL,
    id_perfil INTEGER NOT NULL,
    id_empresa INTEGER,
    id_turno INTEGER,
    id_local INTEGER,
    ativo INTEGER NOT NULL DEFAULT 1,
    trocar_senha INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE tb_designacao_operacional (
    id_designacao INTEGER PRIMARY KEY AUTOINCREMENT,
    id_usuario INTEGER NOT NULL,
    id_empresa INTEGER NOT NULL,
    id_turno INTEGER NOT NULL,
    id_linha INTEGER,
    id_veiculo INTEGER,
    data TEXT NOT NULL,
    inicio TEXT NOT NULL,
    fim TEXT,
    status TEXT NOT NULL DEFAULT 'ATIVA',
    criado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    encerrado_em TEXT,
    id_admin INTEGER
);

CREATE TABLE tb_configuracao (
    idconf INTEGER PRIMARY KEY AUTOINCREMENT,
    chave TEXT NOT NULL,
    valor TEXT NOT NULL
);

CREATE TABLE tb_guia (
    id_guia INTEGER PRIMARY KEY AUTOINCREMENT,
    numero TEXT,
    id_empresa INTEGER,
    id_linha INTEGER,
    id_turno INTEGER,
    id_veiculo INTEGER,
    id_motorista INTEGER,
    hor_ini TEXT,
    hor_fim TEXT,
    roleta01_ini INTEGER,
    roleta01_fim INTEGER,
    roleta2_ini INTEGER,
    roleta2_fim INTEGER,
    observacao TEXT,
    data TEXT
);

CREATE TABLE tb_chegada_saida (
    id_cs INTEGER PRIMARY KEY AUTOINCREMENT,
    id_gui INTEGER,
    id_linha INTEGER,
    carro INTEGER,
    evento TEXT,
    horario TEXT,
    roleta_01 INTEGER,
    roleta_02 INTEGER,
    temperatura INTEGER,
    linha_destino INTEGER,
    destino INTEGER
);

CREATE TABLE tb_map (
    id_registro INTEGER PRIMARY KEY AUTOINCREMENT,
    cod_map INTEGER NOT NULL UNIQUE,
    id_usuario INTEGER NOT NULL,
    id_linha INTEGER,
    id_turno INTEGER NOT NULL,
    data TEXT NOT NULL,
    inicio_jornada_des TEXT NOT NULL,
    fim_jornada_des TEXT,
    observacao TEXT
);

CREATE TABLE tb_item_map (
    id_item INTEGER PRIMARY KEY AUTOINCREMENT,
    idmap INTEGER NOT NULL,
    id_linha INTEGER NOT NULL,
    id_veiculo INTEGER NOT NULL,
    id_motorista INTEGER,
    hor_ini_jor TEXT,
    hor_fim_jor TEXT,
    chegada_ponto TEXT,
    UNIQUE (idmap, id_veiculo)
);

CREATE TABLE tb_viagem (
    id_viagem INTEGER PRIMARY KEY AUTOINCREMENT,
    id_item_registro INTEGER NOT NULL,
    horario_chegada TEXT NOT NULL,
    placa TEXT,
    horario_saida TEXT NOT NULL,
    intervalo INTEGER,
    qtd_pas_ida INTEGER,
    qtd_pas_volta INTEGER
);
"""


class SqliteTestDal:
    """Implementa read/create/update/delete/test_connection como o DAL de produção."""

    def __init__(self) -> None:
        self._conn = sqlite3.connect(":memory:", check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.create_function(
            "CURDATE", 0, lambda: date.today().isoformat()
        )
        self._conn.executescript(SCHEMA_SQL)
        self._in_transaction = False
        self._seed()

    def test_connection(self) -> bool:
        try:
            self._conn.execute("SELECT 1")
            return True
        except sqlite3.Error:
            return False

    def read(self, sql: str, values: Optional[tuple] = None) -> pd.DataFrame:
        try:
            cur = self._conn.execute(sql, values or ())
            rows = cur.fetchall()
            if not rows:
                return pd.DataFrame()
            return pd.DataFrame([dict(r) for r in rows])
        except sqlite3.Error:
            return pd.DataFrame()

    def create(self, sql: str, values: Optional[tuple] = None) -> bool:
        return self._mutate(sql, values)

    def update(self, sql: str, values: Optional[tuple] = None) -> bool:
        return self._mutate(sql, values)

    def delete(self, sql: str, values: Optional[tuple] = None) -> bool:
        return self._mutate(sql, values)

    def _mutate(self, sql: str, values: Optional[tuple]) -> bool:
        try:
            self._conn.execute(sql, values or ())
            if not self._in_transaction:
                self._conn.commit()
            return True
        except sqlite3.Error:
            if not self._in_transaction:
                self._conn.rollback()
            return False

    @contextmanager
    def transaction(self):
        if self._in_transaction:
            yield
            return
        self._in_transaction = True
        try:
            yield
            self._conn.commit()
        except Exception:
            self._conn.rollback()
            raise
        finally:
            self._in_transaction = False

    def _seed(self) -> None:
        c = self._conn
        c.executemany(
            "INSERT INTO tb_perfil (id_perfil, codigo_perfil, descricao) VALUES (?, ?, ?)",
            [
                (1, 1, "Administrador"),
                (2, 2, "Despachante"),
                (3, 3, "Inspetor"),
            ],
        )
        c.execute(
            "INSERT INTO tb_empresa (id_empresa, codigo_empresa, descricao, ativo) "
            "VALUES (1, 1, 'Futuro', 1)"
        )
        c.execute(
            "INSERT INTO tb_empresa (id_empresa, codigo_empresa, descricao, ativo) "
            "VALUES (2, 2, 'Redentor', 1)"
        )
        c.execute(
            "INSERT INTO tb_turno (id_turno, codigo_turno, descricao, ativo) "
            "VALUES (1, 1, 'TURNO 01', 1)"
        )
        c.executemany(
            "INSERT INTO tb_local (id_local, codigo_local, descricao, ativo) VALUES (?, ?, ?, 1)",
            [(1, 10, "Terminal A"), (2, 20, "Terminal B")],
        )
        c.execute(
            """
            INSERT INTO tb_linha (
                id_linha, codigo_linha, id_empresa, descricao,
                id_local_origem, id_local_destino, ativo
            ) VALUES (1, 101, 1, 'Linha 101', 1, 2, 1)
            """
        )
        c.execute(
            """
            INSERT INTO tb_linha (
                id_linha, codigo_linha, id_empresa, descricao,
                id_local_origem, id_local_destino, ativo
            ) VALUES (2, 202, 1, 'Linha 202', 2, 1, 1)
            """
        )
        c.execute(
            """
            INSERT INTO tb_linha (
                id_linha, codigo_linha, id_empresa, descricao,
                id_local_origem, id_local_destino, ativo
            ) VALUES (3, 401, 2, 'Linha Redentor', 1, 2, 1)
            """
        )
        c.execute(
            "INSERT INTO tb_veiculo (id_veiculo, codigo_veiculo, numero_frota, placa, ativo, id_empresa) "
            "VALUES (1, 1, '100', 'ABC1D23', 1, 1)"
        )
        c.execute(
            "INSERT INTO tb_veiculo (id_veiculo, codigo_veiculo, numero_frota, placa, ativo, id_empresa) "
            "VALUES (2, 2, 'C40000', 'XYZ9Z99', 1, 2)"
        )
        c.execute(
            "INSERT INTO tb_motorista (id_motorista, matricula, nome, ativo) "
            "VALUES (1, '50001', 'Motorista Teste', 1)"
        )
        c.executemany(
            "INSERT INTO tb_configuracao (chave, valor) VALUES (?, ?)",
            [
                ("QTD_MAX_TENTATIVAS", "3"),
                ("BLOQUEIO_TENTATIVAS_LOGIN", "1"),
            ],
        )

        senha_ok = hash_senha("Senha@123")
        # Admin — login normal
        c.execute(
            """
            INSERT INTO tb_usuario (
                id_usuario, matricula, nome, senha, id_perfil,
                id_empresa, id_turno, id_local, ativo, trocar_senha
            ) VALUES (1, '1', 'Admin Teste', ?, 1, NULL, NULL, NULL, 1, 0)
            """,
            (senha_ok,),
        )
        # Inspetor
        c.execute(
            """
            INSERT INTO tb_usuario (
                id_usuario, matricula, nome, senha, id_perfil,
                id_empresa, id_turno, id_local, ativo, trocar_senha
            ) VALUES (2, '3', 'Inspetor Teste', ?, 3, NULL, NULL, NULL, 1, 0)
            """,
            (senha_ok,),
        )
        # Despachante com local (entrada/saída)
        c.execute(
            """
            INSERT INTO tb_usuario (
                id_usuario, matricula, nome, senha, id_perfil,
                id_empresa, id_turno, id_local, ativo, trocar_senha
            ) VALUES (3, '2', 'Despachante Teste', ?, 2, 1, 1, 1, 1, 0)
            """,
            (senha_ok,),
        )
        # Primeiro acesso
        c.execute(
            """
            INSERT INTO tb_usuario (
                id_usuario, matricula, nome, senha, id_perfil,
                id_empresa, id_turno, id_local, ativo, trocar_senha
            ) VALUES (4, '99', 'Novo Usuario', ?, 2, 1, 1, 1, 1, 1)
            """,
            (senha_ok,),
        )
        c.commit()


def build_test_app(dal: Any):
    """Flask app de teste com blueprints e DAL injetado."""
    from flask import Flask

    from BackEnd.auth_routes import auth_bp, init_auth_routes
    from BackEnd.designacao_routes import designacoes_bp
    from BackEnd.entrada_saida_routes import entrada_saida_bp
    from BackEnd.guia_routes import guia_bp
    from BackEnd.mapa_routes import mapa_bp
    from BackEnd.security import init_security
    from BackEnd.users_routes import users_bp

    app = Flask(__name__)
    app.config["TESTING"] = True
    app.config["JSON_AS_ASCII"] = False
    init_security(app)
    init_auth_routes(app, lambda: dal)
    app.register_blueprint(auth_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(guia_bp)
    app.register_blueprint(entrada_saida_bp)
    app.register_blueprint(designacoes_bp)
    app.register_blueprint(mapa_bp)
    return app

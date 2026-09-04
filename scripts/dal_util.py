# -*- coding: utf-8 -*-
"""Utilitários para scripts — toda conexão ao banco via BackEnd.dal_factory / DAL."""

from __future__ import annotations

import os
import sys
from typing import Any, Optional, Sequence, Union

import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from BackEnd.dal_factory import create_dal  # noqa: E402
from BackEnd.DAL import DAL  # noqa: E402
from DAL.DAL import _buscar_parametro  # noqa: E402

Params = Optional[Union[Sequence[Any], Any]]


def database_name(dal: DAL) -> str:
    return str(
        _buscar_parametro(dal.config, "bd", "database", "db", "schema", "banco")
    )


def parse_sql_statements(sql: str) -> list[str]:
    stmts: list[str] = []
    for raw in sql.split(";"):
        lines = [
            ln
            for ln in raw.splitlines()
            if ln.strip() and not ln.strip().startswith("--")
        ]
        if not lines:
            continue
        stmt = "\n".join(lines).strip()
        if stmt.upper().startswith("USE "):
            continue
        stmts.append(stmt)
    return stmts


def _preprocess_dump_sql(text: str) -> str:
    """Normaliza dump MySQL/MariaDB para execução via DAL."""
    text = text.replace("utf8mb4_uca1400_ai_ci", "utf8mb4_unicode_ci")
    linhas: list[str] = []
    for ln in text.splitlines():
        strip = ln.strip()
        if not strip or strip.startswith("--"):
            continue
        if strip.startswith("/*"):
            continue
        upper = strip.upper()
        if upper.startswith("LOCK TABLES") or upper.startswith("UNLOCK TABLES"):
            continue
        linhas.append(ln)
    return "\n".join(linhas)


def read_sql_file(path: str) -> list[str]:
    with open(path, encoding="utf-8") as f:
        return parse_sql_statements(_preprocess_dump_sql(f.read()))


def execute_statement(dal: DAL, sql: str, params: Params = None) -> bool | pd.DataFrame:
    comando = sql.strip().split(None, 1)[0].upper()
    if comando in ("SELECT", "SHOW", "DESCRIBE", "EXPLAIN"):
        return dal.read(sql, params)
    if comando == "INSERT":
        return dal.create(sql, params)
    if comando == "DELETE":
        return dal.delete(sql, params)
    return dal.update(sql, params)


def execute_statements(dal: DAL, statements: list[str]) -> None:
    for stmt in statements:
        result = execute_statement(dal, stmt)
        if isinstance(result, pd.DataFrame):
            continue
        if result is False:
            raise RuntimeError(f"Falha ao executar SQL: {stmt[:120]}...")


def execute_sql_file(dal: DAL, path: str) -> None:
    execute_statements(dal, read_sql_file(path))


def execute_sql_files(dal: DAL, *paths: str) -> None:
    for path in paths:
        execute_sql_file(dal, path)


def scalar(dal: DAL, sql: str, params: Params = None, column: Optional[str] = None) -> Any:
    df = dal.read(sql, params)
    if df.empty:
        return None
    if column and column in df.columns:
        return df.iloc[0][column]
    return df.iloc[0, 0]


def column_exists(dal: DAL, table: str, column: str) -> bool:
    n = scalar(
        dal,
        """
        SELECT COUNT(*) AS n
        FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = ? AND TABLE_NAME = ? AND COLUMN_NAME = ?
        """,
        (database_name(dal), table, column),
        "n",
    )
    return int(n or 0) > 0


def table_exists(dal: DAL, table: str) -> bool:
    n = scalar(
        dal,
        """
        SELECT COUNT(*) AS n
        FROM information_schema.TABLES
        WHERE TABLE_SCHEMA = ? AND TABLE_NAME = ?
        """,
        (database_name(dal), table),
        "n",
    )
    return int(n or 0) > 0


def list_tables(dal: DAL) -> list[str]:
    df = dal.read(
        """
        SELECT TABLE_NAME
        FROM information_schema.TABLES
        WHERE TABLE_SCHEMA = ?
          AND TABLE_TYPE = 'BASE TABLE'
        ORDER BY TABLE_NAME
        """,
        (database_name(dal),),
    )
    if df.empty:
        return []
    return [str(v) for v in df["TABLE_NAME"].tolist()]


def truncate_all_tables(dal: DAL) -> int:
    tabelas = list_tables(dal)
    dal.update("SET FOREIGN_KEY_CHECKS = 0")
    for tabela in tabelas:
        dal.update(f"TRUNCATE TABLE `{tabela}`")
    dal.update("SET FOREIGN_KEY_CHECKS = 1")
    return len(tabelas)


class ScriptDal:
    """Adaptador estilo cursor (dict rows) sobre DAL — migração gradual de scripts legados."""

    def __init__(self, dal: DAL) -> None:
        self._dal = dal
        self._last: Optional[pd.DataFrame] = None
        self.lastrowid: Optional[int] = None

    def execute(self, sql: str, params: Params = None) -> None:
        comando = sql.strip().split(None, 1)[0].upper()
        if comando in ("SELECT", "SHOW", "DESCRIBE", "EXPLAIN"):
            self._last = self._dal.read(sql, params)
            self.lastrowid = None
            return
        if comando == "INSERT":
            ok = self._dal.create(sql, params)
        elif comando == "DELETE":
            ok = self._dal.delete(sql, params)
        else:
            ok = self._dal.update(sql, params)
        if not ok:
            raise RuntimeError(f"Falha SQL: {sql[:120]}...")
        self._last = None
        row = self._dal.read("SELECT LAST_INSERT_ID() AS id")
        self.lastrowid = int(row.iloc[0]["id"]) if not row.empty else None

    def fetchone(self) -> Optional[dict[str, Any]]:
        if self._last is None or self._last.empty:
            return None
        return self._last.iloc[0].to_dict()

    def fetchall(self) -> list[dict[str, Any]]:
        if self._last is None or self._last.empty:
            return []
        return self._last.to_dict(orient="records")

    def __enter__(self) -> ScriptDal:
        return self

    def __exit__(self, *args: object) -> None:
        return None


__all__ = [
    "BASE_DIR",
    "ScriptDal",
    "column_exists",
    "create_dal",
    "database_name",
    "execute_sql_file",
    "execute_sql_files",
    "execute_statement",
    "execute_statements",
    "list_tables",
    "parse_sql_statements",
    "read_sql_file",
    "scalar",
    "table_exists",
    "truncate_all_tables",
]

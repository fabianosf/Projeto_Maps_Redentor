#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Aplica dump-crip.sql no banco MariaDB 'crip' (mesmo servidor do map).

Uso:
    py -3 scripts/aplicar_dump_crip.py
    py -3 scripts/aplicar_dump_crip.py --dump caminho/para/dump-crip.sql
"""

from __future__ import annotations

import argparse
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

sys.path.insert(0, os.path.join(BASE_DIR, "scripts"))

from dal_util import create_dal, execute_sql_file, scalar  # noqa: E402


def _resolver_dump(path_arg: str | None) -> str:
    candidatos = [
        path_arg,
        r"C:\dump-crip.sql",
        os.path.join(BASE_DIR, "dump-crip.sql"),
        os.path.join(BASE_DIR, "database", "dump-crip.sql"),
        os.path.join(BASE_DIR, "BackEnd", "dump-crip.sql"),
    ]
    for caminho in candidatos:
        if caminho and os.path.isfile(caminho):
            return os.path.abspath(caminho)
    raise FileNotFoundError(
        "Arquivo dump-crip.sql não encontrado. Informe --dump <caminho> "
        f"(ex.: C:\\dump-crip.sql) ou coloque-o na raiz do projeto ({BASE_DIR})."
    )


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(description="Aplica dump no banco crip")
    parser.add_argument(
        "--dump",
        help="Caminho do arquivo dump-crip.sql (padrão: raiz do projeto)",
    )
    args = parser.parse_args()

    dump_path = _resolver_dump(args.dump)
    print(f"Dump: {dump_path}")

    dal = create_dal()
    print(f"Servidor: {dal.connection_string}")

    db_exists = scalar(
        dal,
        "SELECT COUNT(*) AS n FROM information_schema.schemata WHERE schema_name = ?",
        ("crip",),
        column="n",
    )
    if int(db_exists or 0) == 0:
        print("Banco 'crip' não existe — criando...")
        if not dal.update("CREATE DATABASE IF NOT EXISTS crip CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"):
            raise RuntimeError("Falha ao criar banco crip")

    antes = scalar(
        dal,
        """
        SELECT COUNT(*) AS n
        FROM information_schema.tables
        WHERE table_schema = 'crip'
        """,
        column="n",
    )
    print(f"Tabelas em crip (antes): {antes}")

    dal.update("USE crip")
    print("Aplicando dump...")
    execute_sql_file(dal, dump_path)

    depois = scalar(
        dal,
        """
        SELECT COUNT(*) AS n
        FROM information_schema.tables
        WHERE table_schema = 'crip'
        """,
        column="n",
    )
    print(f"Tabelas em crip (depois): {depois}")

    tabelas = dal.read(
        """
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'crip'
        ORDER BY table_name
        """
    )
    if not tabelas.empty:
        print("Tabelas criadas:")
        for nome in tabelas["table_name"].tolist():
            print(f"  - {nome}")

    print("OK — dump aplicado com sucesso.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print(f"ERRO: {exc}", file=sys.stderr)
        sys.exit(1)

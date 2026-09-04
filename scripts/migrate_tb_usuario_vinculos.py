# -*- coding: utf-8 -*-
"""Aplica schema_migrate_tb_usuario_vinculos.sql no banco map."""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dal_util import BASE_DIR, column_exists, create_dal, execute_sql_file

SQL_PATH = os.path.join(BASE_DIR, "database", "schema_migrate_tb_usuario_vinculos.sql")


def main() -> int:
    dal = create_dal()
    try:
        if column_exists(dal, "tb_usuario", "id_empresa"):
            print("Colunas de vinculo ja existem em tb_usuario — skip.")
            return 0

        with open(SQL_PATH, encoding="utf-8") as f:
            sql = f.read()

        for stmt in [
            s.strip()
            for s in sql.split(";")
            if s.strip() and not s.strip().startswith("--")
        ]:
            if stmt.upper().startswith("USE "):
                continue
            print(f"Executando: {stmt[:60]}...")
            dal.update(stmt)

        print("Migracao tb_usuario vinculos concluida.")
        return 0
    except Exception as exc:
        print(f"ERRO: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

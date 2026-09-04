# -*- coding: utf-8 -*-
"""Aplica schema_migrate_tb_guia_roleta2.sql no banco map."""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dal_util import BASE_DIR, column_exists, create_dal, execute_sql_file

SQL_PATH = os.path.join(BASE_DIR, "database", "schema_migrate_tb_guia_roleta2.sql")


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    dal = create_dal()
    for col in ("roleta2_ini", "roleta2_fim"):
        if column_exists(dal, "tb_guia", col):
            print(f"Coluna {col} já existe — ignorando migração.")
            return 0

    execute_sql_file(dal, SQL_PATH)
    print("Migração tb_guia roleta2_ini / roleta2_fim aplicada com sucesso.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

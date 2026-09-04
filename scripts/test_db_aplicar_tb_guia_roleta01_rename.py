# -*- coding: utf-8 -*-
"""Renomeia tb_guia.roleta_ini/fim para roleta01_ini/fim."""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dal_util import BASE_DIR, column_exists, create_dal, execute_sql_file

SQL_PATH = os.path.join(BASE_DIR, "database", "schema_migrate_tb_guia_roleta01_rename.sql")


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    dal = create_dal()
    if column_exists(dal, "tb_guia", "roleta01_ini"):
        print("Colunas roleta01_ini / roleta01_fim já existem — migração ignorada.")
        return 0
    if not column_exists(dal, "tb_guia", "roleta_ini"):
        print("Coluna roleta_ini não encontrada — nada a renomear.")
        return 1

    execute_sql_file(dal, SQL_PATH)
    print("Migração roleta01_ini / roleta01_fim aplicada com sucesso.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

# -*- coding: utf-8 -*-
"""Aplica schema_migrate_tb_guia.sql no banco map."""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dal_util import BASE_DIR, ScriptDal, create_dal, execute_sql_file, table_exists

SQL_PATH = os.path.join(BASE_DIR, "database", "schema_migrate_tb_guia.sql")
SQL_ADD_DATA = os.path.join(BASE_DIR, "database", "schema_migrate_tb_guia_add_data.sql")
SQL_DATA_DATETIME = os.path.join(
    BASE_DIR, "database", "schema_migrate_tb_guia_data_datetime.sql"
)


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    dal = create_dal()
    execute_sql_file(dal, SQL_PATH)
    execute_sql_file(dal, SQL_ADD_DATA)
    execute_sql_file(dal, SQL_DATA_DATETIME)
    cur = ScriptDal(dal)

    print(f"tb_guia existe: {table_exists(dal, 'tb_guia')}")
    cur.execute("DESCRIBE tb_guia")
    for row in cur.fetchall():
        print(f"  {row['Field']:14} {row['Type']}")

    print("Migração tb_guia aplicada com sucesso.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

# -*- coding: utf-8 -*-
"""Aplica schema_migrate_tb_chegada_saida.sql no banco map."""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dal_util import BASE_DIR, ScriptDal, create_dal, execute_sql_file, table_exists

SQL_PATH = os.path.join(BASE_DIR, "database", "schema_migrate_tb_chegada_saida.sql")


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    dal = create_dal()
    execute_sql_file(dal, SQL_PATH)
    cur = ScriptDal(dal)

    print(f"tb_chegada_saida existe: {table_exists(dal, 'tb_chegada_saida')}")
    cur.execute("DESCRIBE tb_chegada_saida")
    for row in cur.fetchall():
        print(f"  {row['Field']:14} {row['Type']}")

    print("Migração tb_chegada_saida aplicada com sucesso.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

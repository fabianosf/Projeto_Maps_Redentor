# -*- coding: utf-8 -*-
"""Aplica schema_migrate_tb_chegada_saida_roleta.sql no banco map."""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dal_util import BASE_DIR, ScriptDal, create_dal, execute_sql_file

SQL_PATH = os.path.join(BASE_DIR, "database", "schema_migrate_tb_chegada_saida_roleta.sql")


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    dal = create_dal()
    execute_sql_file(dal, SQL_PATH)
    cur = ScriptDal(dal)

    cur.execute("DESCRIBE tb_chegada_saida")
    print("Colunas tb_chegada_saida:")
    for row in cur.fetchall():
        print(f"  {row['Field']:14} {row['Type']}")

    print("Migração roleta_01 / roleta_02 aplicada com sucesso.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

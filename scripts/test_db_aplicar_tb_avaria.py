# -*- coding: utf-8 -*-
"""Aplica schema_migrate_tb_avaria.sql no banco map."""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dal_util import ScriptDal, create_dal, execute_sql_file, table_exists

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SQL_PATH = os.path.join(BASE, "database", "schema_migrate_tb_avaria.sql")


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    dal = create_dal()
    execute_sql_file(dal, SQL_PATH)
    cur = ScriptDal(dal)

    for table in ("tb_tip_avaria", "tb_avaria"):
        print(f"{table} existe: {table_exists(dal, table)}")
        cur.execute(f"DESCRIBE {table}")
        for row in cur.fetchall():
            print(f"  {row['Field']:12} {row['Type']}")

    print("Migração tb_tip_avaria / tb_avaria aplicada com sucesso.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

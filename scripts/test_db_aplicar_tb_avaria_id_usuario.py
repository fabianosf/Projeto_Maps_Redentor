# -*- coding: utf-8 -*-
"""Aplica schema_migrate_tb_avaria_id_usuario.sql no banco map."""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dal_util import BASE_DIR, ScriptDal, create_dal, database_name, execute_sql_file

SQL_PATH = os.path.join(BASE_DIR, "database", "schema_migrate_tb_avaria_id_usuario.sql")


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    dal = create_dal()
    db = database_name(dal)
    execute_sql_file(dal, SQL_PATH)
    cur = ScriptDal(dal)

    cur.execute("DESCRIBE tb_avaria")
    print("tb_avaria:")
    for row in cur.fetchall():
        print(f"  {row['Field']:12} {row['Type']}")

    cur.execute(
        """
        SELECT CONSTRAINT_NAME, COLUMN_NAME, REFERENCED_TABLE_NAME,
               REFERENCED_COLUMN_NAME
        FROM information_schema.KEY_COLUMN_USAGE
        WHERE TABLE_SCHEMA = ?
          AND TABLE_NAME = 'tb_avaria'
          AND REFERENCED_TABLE_NAME IS NOT NULL
        ORDER BY CONSTRAINT_NAME
        """,
        (db,),
    )
    print("FKs:")
    for row in cur.fetchall():
        print(
            f"  {row['CONSTRAINT_NAME']}: "
            f"{row['COLUMN_NAME']} -> "
            f"{row['REFERENCED_TABLE_NAME']}.{row['REFERENCED_COLUMN_NAME']}"
        )

    print("Migração tb_avaria (id_usuario) aplicada com sucesso.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

# -*- coding: utf-8 -*-
"""Aplica migrações tb_indicador e remoção tb_map/tb_item_map/tb_viagem."""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dal_util import BASE_DIR, ScriptDal, create_dal, execute_sql_files, table_exists

SQL_FILES = [
    os.path.join(BASE_DIR, "database", "schema_migrate_drop_map_viagem.sql"),
    os.path.join(BASE_DIR, "database", "schema_migrate_tb_indicador.sql"),
]


def describe_table(cur: ScriptDal, name: str) -> None:
    print(f"\n{name}:")
    cur.execute(f"DESCRIBE {name}")
    for row in cur.fetchall():
        print(f"  {row['Field']:14} {row['Type']}")


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    dal = create_dal()
    execute_sql_files(dal, *SQL_FILES)
    cur = ScriptDal(dal)

    for dropped in ("tb_viagem", "tb_item_map", "tb_map"):
        print(f"{dropped} existe: {table_exists(dal, dropped)}")

    for created in ("tb_indicador", "tb_ind_perf"):
        print(f"{created} existe: {table_exists(dal, created)}")

    if table_exists(dal, "tb_indicador"):
        describe_table(cur, "tb_indicador")
    if table_exists(dal, "tb_ind_perf"):
        describe_table(cur, "tb_ind_perf")

    print("\nMigração indicadores aplicada com sucesso.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

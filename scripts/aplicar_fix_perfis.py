# -*- coding: utf-8 -*-
"""Corrige descrições de perfil no banco map (2=Despachante, 3=Inspetor)."""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dal_util import create_dal, execute_sql_file

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SQL_PATH = os.path.join(BASE, "database", "schema_migrate_fix_perfis.sql")


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    dal = create_dal()
    execute_sql_file(dal, SQL_PATH)

    df = dal.read(
        """
        SELECT id_perfil, codigo_perfil, descricao
        FROM tb_perfil
        ORDER BY codigo_perfil
        """
    )
    print("Perfis após correção:")
    for _, row in df.iterrows():
        print(
            f"  id={row['id_perfil']}  codigo={row['codigo_perfil']}  "
            f"{row['descricao']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

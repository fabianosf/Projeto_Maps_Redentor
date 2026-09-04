# -*- coding: utf-8 -*-
"""Limpa e recarrega cadastros base do banco map (Proj_Map)."""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dal_util import BASE_DIR, ScriptDal, create_dal, execute_sql_file, scalar, truncate_all_tables

SQL_PATH = os.path.join(BASE_DIR, "database", "schema_reseed_proj_map.sql")


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    dal = create_dal()
    n = truncate_all_tables(dal)
    print(f"Tabelas truncadas: {n}")

    execute_sql_file(dal, SQL_PATH)

    for table in (
        "tb_empresa",
        "tb_turno",
        "tb_perfil",
        "tb_local",
        "tb_linha",
    ):
        count = scalar(dal, f"SELECT COUNT(*) AS n FROM {table}", column="n")
        print(f"{table}: {count} registro(s)")

    cur = ScriptDal(dal)
    cur.execute(
        """
        SELECT l.id_linha, l.codigo_linha, l.descricao,
               lo.codigo_local AS origem, ld.codigo_local AS destino,
               l.ativo
        FROM tb_linha l
        JOIN tb_local lo ON lo.id_local = l.id_local_origem
        JOIN tb_local ld ON ld.id_local = l.id_local_destino
        ORDER BY l.id_linha
        """
    )
    print("\nLinhas:")
    for row in cur.fetchall():
        print(
            f"  id={row['id_linha']} cod={row['codigo_linha']} "
            f"{row['descricao']} ({row['origem']}->{row['destino']}) "
            f"ativo={row['ativo']}"
        )

    print("\nReseed Proj_Map concluído.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

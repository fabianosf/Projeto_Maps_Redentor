# -*- coding: utf-8 -*-
"""Aplica migrações operacionais (avaria.texto, chegada_saida.horario, tipos avaria)."""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dal_util import BASE_DIR, column_exists, create_dal, execute_sql_file, scalar

MIGRATIONS = [
    "schema_migrate_tb_avaria_texto.sql",
    "schema_migrate_tb_chegada_saida_horario.sql",
    "schema_seed_tip_avaria.sql",
]


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    dal = create_dal()

    if not column_exists(dal, "tb_avaria", "texto"):
        dal.update(
            "ALTER TABLE tb_avaria ADD COLUMN texto VARCHAR(500) NULL "
            "COMMENT 'Texto livre da mensagem' AFTER data"
        )
        print("tb_avaria.texto: adicionada")
    else:
        print("tb_avaria.texto: já existe")

    if not column_exists(dal, "tb_chegada_saida", "horario"):
        dal.update(
            "ALTER TABLE tb_chegada_saida ADD COLUMN horario VARCHAR(5) NULL "
            "COMMENT 'Horário HH:MM' AFTER evento"
        )
        print("tb_chegada_saida.horario: adicionada")
    else:
        print("tb_chegada_saida.horario: já existe")

    for name in MIGRATIONS[2:]:
        path = os.path.join(BASE_DIR, "database", name)
        execute_sql_file(dal, path)
        print(f"{name}: aplicado")

    n = scalar(dal, "SELECT COUNT(*) AS n FROM tb_tip_avaria", column="n")
    print(f"tb_tip_avaria: {n} tipo(s)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

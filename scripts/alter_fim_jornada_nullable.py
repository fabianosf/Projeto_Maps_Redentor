"""Torna tb_map.fim_jornada_des NULLABLE (FIM DE JORNADA opcional)."""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dal_util import ScriptDal, create_dal, database_name


def main() -> None:
    dal = create_dal()
    db = database_name(dal)
    cur = ScriptDal(dal)

    dal.update("SET SESSION lock_wait_timeout = 30")
    try:
        dal.update(
            "ALTER TABLE tb_map "
            "MODIFY COLUMN fim_jornada_des DATETIME NULL "
            "COMMENT 'Fim da jornada (desejado/planejado) — opcional'"
        )
        print("ALTER OK")
    except Exception as exc:
        print("ALTER ERR:", type(exc).__name__, exc)

    cur.execute(
        "SELECT IS_NULLABLE, COLUMN_TYPE "
        "FROM information_schema.COLUMNS "
        "WHERE TABLE_SCHEMA=? AND TABLE_NAME=? AND COLUMN_NAME=?",
        (db, "tb_map", "fim_jornada_des"),
    )
    print("coluna:", cur.fetchone())


if __name__ == "__main__":
    main()

"""Torna tb_map.fim_jornada_des NULLABLE (FIM DE JORNADA opcional)."""

from __future__ import annotations

import pymysql


def main() -> None:
    conn = pymysql.connect(
        host="10.1.1.29",
        port=3306,
        user="alberto",
        password="at5001",
        database="map",
        connect_timeout=8,
        autocommit=True,
        read_timeout=90,
        write_timeout=90,
    )
    cur = conn.cursor()
    cur.execute("SET SESSION lock_wait_timeout = 30")
    try:
        cur.execute(
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
        "WHERE TABLE_SCHEMA=%s AND TABLE_NAME=%s AND COLUMN_NAME=%s",
        ("map", "tb_map", "fim_jornada_des"),
    )
    print("coluna:", cur.fetchone())
    conn.close()


if __name__ == "__main__":
    main()

"""Adiciona coluna placa (HH:MM) em tb_viagem, se ainda nao existir."""

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
        charset="utf8mb4",
    )
    cur = conn.cursor()
    cur.execute(
        """
        SELECT COUNT(*) FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = 'map' AND TABLE_NAME = 'tb_viagem' AND COLUMN_NAME = 'placa'
        """
    )
    exists = int(cur.fetchone()[0]) > 0
    if exists:
        print("COLUNA placa JA EXISTE")
    else:
        cur.execute(
            """
            ALTER TABLE tb_viagem
            ADD COLUMN placa VARCHAR(5) NULL
                COMMENT 'Horario auxiliar no formato HH:MM (campo Placa da UI)'
                AFTER horario_chegada
            """
        )
        print("COLUNA placa ADICIONADA")
    cur.execute("DESCRIBE tb_viagem")
    print(cur.fetchall())
    conn.close()


if __name__ == "__main__":
    main()

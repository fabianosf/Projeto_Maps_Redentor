"""Garante turnos em tb_turno (padrão TURNO 01)."""

from __future__ import annotations

import pymysql

TURNOS = [(1, "TURNO 01"), (2, "TURNO 02"), (3, "TURNO 03")]


def main() -> None:
    conn = pymysql.connect(
        host="10.1.1.29",
        port=3306,
        user="alberto",
        password="at5001",
        database="map",
        connect_timeout=8,
        autocommit=True,
    )
    cur = conn.cursor()
    for codigo, nome in TURNOS:
        cur.execute("SELECT id_turno FROM tb_turno WHERE codigo_turno=%s", (codigo,))
        row = cur.fetchone()
        if row:
            cur.execute(
                "UPDATE tb_turno SET descricao=%s, ativo=1 WHERE codigo_turno=%s",
                (nome, codigo),
            )
        else:
            cur.execute(
                "INSERT INTO tb_turno (codigo_turno, descricao, ativo) VALUES (%s, %s, 1)",
                (codigo, nome),
            )
    cur.execute(
        "SELECT id_turno, codigo_turno, descricao, ativo FROM tb_turno ORDER BY codigo_turno"
    )
    print(cur.fetchall())
    conn.close()


if __name__ == "__main__":
    main()

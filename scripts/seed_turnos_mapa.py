"""Garante turnos em tb_turno (padrão TURNO 01)."""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dal_util import ScriptDal, create_dal


TURNOS = [(1, "TURNO 01"), (2, "TURNO 02"), (3, "TURNO 03")]


def main() -> None:
    dal = create_dal()
    cur = ScriptDal(dal)

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


if __name__ == "__main__":
    main()

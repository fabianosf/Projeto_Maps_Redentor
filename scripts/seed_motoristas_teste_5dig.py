"""Cadastra matrículas de teste (5 dígitos) em tb_motorista sem sobrescrever existentes."""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dal_util import ScriptDal, create_dal

MOTORISTAS = [
    ("10001", "Motorista Teste 10001"),
    ("10002", "Motorista Teste 10002"),
    ("10003", "Motorista Teste 10003"),
    ("10004", "Motorista Teste 10004"),
    ("10005", "Motorista Teste 10005"),
    ("10006", "Motorista Teste 10006"),
]


def main() -> None:
    dal = create_dal()
    cur = ScriptDal(dal)
    inseridos = []

    for matricula, nome in MOTORISTAS:
        cur.execute(
            "SELECT id_motorista FROM tb_motorista WHERE matricula=%s",
            (matricula,),
        )
        if cur.fetchone():
            print(f"SKIP: {matricula} (ja existe)")
            continue
        cur.execute(
            "INSERT INTO tb_motorista (matricula, nome, ativo) VALUES (%s, %s, 1)",
            (matricula, nome),
        )
        inseridos.append((matricula, nome))
        print(f"INSERT: {matricula} / {nome}")

    print("INSERIDOS:", inseridos)
    cur.execute(
        """
        SELECT id_motorista, matricula, nome, ativo
        FROM tb_motorista
        WHERE matricula IN (%s,%s,%s,%s,%s,%s)
        ORDER BY matricula
        """,
        tuple(m[0] for m in MOTORISTAS),
    )
    print("CONFIRMADOS:", cur.fetchall())


if __name__ == "__main__":
    main()

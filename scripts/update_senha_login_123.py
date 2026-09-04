"""Atualiza senha de login dos usuarios ativos para '123' (bcrypt)."""

from __future__ import annotations

import os
import sys

import bcrypt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dal_util import ScriptDal, create_dal

NOVA_SENHA = "123"


def main() -> None:
    hashed = bcrypt.hashpw(NOVA_SENHA.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode(
        "utf-8"
    )
    dal = create_dal()
    cur = ScriptDal(dal)

    cur.execute(
        "SELECT id_usuario, matricula, nome, ativo, trocar_senha FROM tb_usuario ORDER BY matricula"
    )
    usuarios = cur.fetchall()
    print("ANTES:", usuarios)

    cur.execute(
        """
        UPDATE tb_usuario
        SET senha = %s, trocar_senha = 0
        WHERE ativo = 1
        """,
        (hashed,),
    )

    cur.execute("SELECT matricula, senha, trocar_senha FROM tb_usuario WHERE ativo = 1")
    for row in cur.fetchall():
        ok = bcrypt.checkpw(NOVA_SENHA.encode("utf-8"), row["senha"].encode("utf-8"))
        print(f"CHECK {row['matricula']}: ok={ok} trocar_senha={row['trocar_senha']}")


if __name__ == "__main__":
    main()

"""Atualiza senha de login dos usuarios ativos para '123' (bcrypt)."""

from __future__ import annotations

import bcrypt
import pymysql

NOVA_SENHA = "123"


def main() -> None:
    hashed = bcrypt.hashpw(NOVA_SENHA.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode(
        "utf-8"
    )
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
        "SELECT id_usuario, matricula, nome, ativo, trocar_senha FROM tb_usuario ORDER BY matricula"
    )
    usuarios = cur.fetchall()
    print("ANTES:", usuarios)

    # Atualiza todos os ativos; trocar_senha=0 para permitir login direto
    cur.execute(
        """
        UPDATE tb_usuario
        SET senha = %s, trocar_senha = 0
        WHERE ativo = 1
        """,
        (hashed,),
    )
    print("ROWS_UPDATED:", cur.rowcount)

    # Confere bcrypt
    cur.execute("SELECT matricula, senha, trocar_senha FROM tb_usuario WHERE ativo = 1")
    for matricula, senha, trocar in cur.fetchall():
        ok = bcrypt.checkpw(NOVA_SENHA.encode("utf-8"), senha.encode("utf-8"))
        print(f"CHECK {matricula}: ok={ok} trocar_senha={trocar}")

    conn.close()


if __name__ == "__main__":
    main()

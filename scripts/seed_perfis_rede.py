# -*- coding: utf-8 -*-
"""Cadastra perfis na base map da rede (10.1.1.29) com usuário alberto."""

from __future__ import annotations

import sys

import pymysql

HOST = "10.1.1.29"
PORT = 3306
USER = "alberto"
PASSWORD = "at5001"
DATABASE = "map"  # base RedMapa (tb_perfil); DB_SCRI é outro sistema

PERFIS = [
    (1, "Administrador"),
    (2, "Inspetor"),
    (3, "Despachante"),
]


def main() -> int:
    print(f"Conectando {USER}@{HOST}:{PORT}/{DATABASE} ...")
    conn = pymysql.connect(
        host=HOST,
        port=PORT,
        user=USER,
        password=PASSWORD,
        database=DATABASE,
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
        connect_timeout=15,
    )
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT TABLE_NAME
                FROM information_schema.TABLES
                WHERE TABLE_SCHEMA = %s AND TABLE_TYPE = 'BASE TABLE'
                ORDER BY TABLE_NAME
                """,
                (DATABASE,),
            )
            tabelas = [r["TABLE_NAME"] for r in cur.fetchall()]
            print("Tabelas:", ", ".join(tabelas))

            print("\nContagem atual:")
            sujas = []
            for tabela in tabelas:
                cur.execute(f"SELECT COUNT(*) AS qtd FROM `{tabela}`")
                qtd = int(cur.fetchone()["qtd"])
                print(f"  {tabela}: {qtd}" + ("" if qtd == 0 else "  << NÃO VAZIA"))
                if qtd > 0:
                    sujas.append((tabela, qtd))

            if sujas:
                print("\nLimpando tabelas com dados (TRUNCATE)...")
                cur.execute("SET FOREIGN_KEY_CHECKS = 0")
                for tabela, qtd in sujas:
                    cur.execute(f"TRUNCATE TABLE `{tabela}`")
                    print(f"  TRUNCATE {tabela} ({qtd})")
                cur.execute("SET FOREIGN_KEY_CHECKS = 1")
                conn.commit()
            else:
                print("\nTodas as tabelas estão vazias.")

            print("\nRechecagem:")
            for tabela in tabelas:
                cur.execute(f"SELECT COUNT(*) AS qtd FROM `{tabela}`")
                qtd = int(cur.fetchone()["qtd"])
                print(f"  {tabela}: {qtd}")
                if qtd != 0:
                    print(f"ERRO: {tabela} não está vazia.")
                    return 1

            print("\nInserindo perfis em tb_perfil...")
            for codigo, descricao in PERFIS:
                cur.execute(
                    """
                    INSERT INTO tb_perfil (codigo_perfil, descricao)
                    VALUES (%s, %s)
                    """,
                    (codigo, descricao),
                )
                print(f"  {codigo} — {descricao}")
            conn.commit()

            cur.execute(
                """
                SELECT id_perfil, codigo_perfil, descricao
                FROM tb_perfil
                ORDER BY codigo_perfil
                """
            )
            print("\nPerfis cadastrados:")
            for row in cur.fetchall():
                print(
                    f"  id_perfil={row['id_perfil']}  "
                    f"codigo={row['codigo_perfil']}  "
                    f"{row['descricao']}"
                )
            print("\nConcluído.")
            return 0
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())

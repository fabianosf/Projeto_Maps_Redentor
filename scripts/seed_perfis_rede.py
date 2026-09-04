# -*- coding: utf-8 -*-
"""Cadastra perfis na base map via DAL."""

from __future__ import annotations

import sys

import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dal_util import ScriptDal, create_dal, list_tables, truncate_all_tables

PERFIS = [
    (1, "Administrador"),
    (2, "Despachante"),
    (3, "Inspetor"),
]


def main() -> int:
    dal = create_dal()
    print(f"Conectando via DAL ({dal.connection_string}) ...")

    tabelas = list_tables(dal)
    print("Tabelas:", ", ".join(tabelas))

    print("\nContagem atual:")
    cur = ScriptDal(dal)
    sujas = []
    for tabela in tabelas:
        cur.execute(f"SELECT COUNT(*) AS qtd FROM `{tabela}`")
        qtd = int(cur.fetchone()["qtd"])
        print(f"  {tabela}: {qtd}" + ("" if qtd == 0 else "  << NÃO VAZIA"))
        if qtd > 0:
            sujas.append((tabela, qtd))

    if sujas:
        print("\nLimpando tabelas com dados (TRUNCATE)...")
        truncate_all_tables(dal)
        for tabela, qtd in sujas:
            print(f"  TRUNCATE {tabela} ({qtd})")
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


if __name__ == "__main__":
    raise SystemExit(main())

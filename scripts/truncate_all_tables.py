# -*- coding: utf-8 -*-
"""Apaga todos os registros de todas as tabelas do banco map."""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dal_util import create_dal, database_name, list_tables


def main() -> int:
    dal = create_dal()
    if not dal.test_connection():
        print(f"Falha na conexão com o banco {database_name(dal)}.")
        return 1

    tabelas = list_tables(dal)
    if not tabelas:
        print(f"Nenhuma tabela encontrada no banco {database_name(dal)}.")
        return 0

    print("Tabelas:", ", ".join(tabelas))

    if not dal.update("SET FOREIGN_KEY_CHECKS = 0"):
        print("Aviso: não foi possível desabilitar FOREIGN_KEY_CHECKS.")

    for tabela in tabelas:
        antes = dal.read(f"SELECT COUNT(*) AS qtd FROM `{tabela}`")
        qtd = int(antes.iloc[0]["qtd"]) if not antes.empty else 0
        ok = dal.update(f"TRUNCATE TABLE `{tabela}`")
        status = "OK" if ok else "FALHA"
        print(f"  TRUNCATE {tabela}: {qtd} registro(s) removido(s) — {status}")

    dal.update("SET FOREIGN_KEY_CHECKS = 1")

    print("\nContagem após limpeza:")
    for tabela in tabelas:
        depois = dal.read(f"SELECT COUNT(*) AS qtd FROM `{tabela}`")
        qtd = int(depois.iloc[0]["qtd"]) if not depois.empty else -1
        print(f"  {tabela}: {qtd}")

    print("\nConcluído.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

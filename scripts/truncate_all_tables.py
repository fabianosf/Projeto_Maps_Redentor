# -*- coding: utf-8 -*-
"""Apaga todos os registros de todas as tabelas do banco map."""

from __future__ import annotations

import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)

from BackEnd.DAL import DAL  # noqa: E402


def main() -> int:
    pasta = os.path.join(BASE, "DAL", "arquivos_crip")
    dal = DAL(config_arquivo="map_MariaDB", pasta_conf=pasta, sgbd="mariadb")
    if not dal.test_connection():
        print("Falha na conexão com o banco map.")
        return 1

    tabelas_df = dal.read(
        """
        SELECT TABLE_NAME
        FROM information_schema.TABLES
        WHERE TABLE_SCHEMA = 'map'
          AND TABLE_TYPE = 'BASE TABLE'
        ORDER BY TABLE_NAME
        """
    )
    if tabelas_df.empty:
        print("Nenhuma tabela encontrada no banco map.")
        return 0

    tabelas = [str(r) for r in tabelas_df["TABLE_NAME"].tolist()]
    print("Tabelas:", ", ".join(tabelas))

    # Desabilita FKs, trunca tudo, reabilita
    if not dal.update("SET FOREIGN_KEY_CHECKS = 0"):
        print("Aviso: não foi possível desabilitar FOREIGN_KEY_CHECKS.")

    for tabela in tabelas:
        # Contagem antes
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

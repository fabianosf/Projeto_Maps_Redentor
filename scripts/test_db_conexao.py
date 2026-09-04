# -*- coding: utf-8 -*-
"""
Teste de conexão MariaDB — banco map (RedMapa).

Uso:
    py -3 scripts/test_db_conexao.py
"""

from __future__ import annotations

import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dal_util import column_exists, create_dal, database_name, scalar

from BackEnd.DAL import DatabaseConnectionError  # noqa: E402


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    print("=" * 60)
    print("Teste de conexão — MariaDB / RedMapa")
    print("=" * 60)

    t0 = time.perf_counter()
    try:
        print("Conectando via DAL...")
        dal = create_dal()
        db = database_name(dal)
        print(f"  Conexão   : {dal.connection_string}")
        print(f"  Banco     : {db}")
        print("-" * 60)

        if not dal.test_connection():
            raise DatabaseConnectionError("test_connection() retornou False")

        elapsed = time.perf_counter() - t0
        print(f"OK — conexão estabelecida em {elapsed:.2f}s")

        ping = scalar(dal, "SELECT 1 AS ok", column="ok")
        print(f"  Ping SQL : {ping}")

        info_df = dal.read("SELECT VERSION() AS versao, DATABASE() AS banco, USER() AS usuario")
        info = info_df.iloc[0]
        print(f"  Versão   : {info['versao']}")
        print(f"  Banco    : {info['banco']}")
        print(f"  Sessão   : {info['usuario']}")

        n_usu = scalar(dal, "SELECT COUNT(*) AS n FROM tb_usuario", column="n")
        print(f"  Usuários : {n_usu} registro(s) em tb_usuario")

        cfg_df = dal.read(
            """
            SELECT chave, valor FROM tb_configuracao
            WHERE chave = 'QTD_MAX_TENTATIVAS'
            LIMIT 1
            """
        )
        if not cfg_df.empty:
            print(f"  Config   : QTD_MAX_TENTATIVAS = {cfg_df.iloc[0]['valor']}")
        else:
            print("  Config   : QTD_MAX_TENTATIVAS não encontrada")

        print("-" * 60)
        print("Colunas de vínculo em tb_usuario (via information_schema):")
        for col in ("id_empresa", "id_turno", "id_local"):
            existe = column_exists(dal, "tb_usuario", col)
            print(f"  {col:12} : {'EXISTE' if existe else 'AUSENTE'}")

        print("-" * 60)
        print("Teste concluído com sucesso.")
        return 0

    except DatabaseConnectionError as exc:
        elapsed = time.perf_counter() - t0
        print(f"FALHA — DatabaseConnectionError após {elapsed:.2f}s")
        print(f"  {exc}")
        print()
        print("Sugestões:")
        print("  • Verifique VPN/rede até o servidor MariaDB")
        print("  • Confirme se o MariaDB aceita conexões remotas do seu IP")
        return 1

    except Exception as exc:
        elapsed = time.perf_counter() - t0
        print(f"FALHA — {type(exc).__name__} após {elapsed:.2f}s")
        print(f"  {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())

# -*- coding: utf-8 -*-
"""
Libera locks pendentes em tb_usuario e aplica schema_migrate_tb_usuario_vinculos.sql.

Uso:
    py -3 scripts/test_db_aplicar_vinculos.py
    py -3 scripts/test_db_aplicar_vinculos.py --apenas-teste
"""

from __future__ import annotations

import argparse
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dal_util import BASE_DIR, column_exists, create_dal, database_name, execute_sql_file, scalar

SQL_PATH = os.path.join(BASE_DIR, "database", "schema_migrate_tb_usuario_vinculos.sql")


def _db_user(dal) -> str:
    return dal.connection_string.split("://", 1)[1].split(":", 1)[0]


def matar_alters_travados(dal, db_user: str) -> int:
    df = dal.read("SHOW FULL PROCESSLIST")
    mortos = 0
    for _, row in df.iterrows():
        info = str(row.get("Info") or "").lower()
        if row.get("User") != db_user:
            continue
        if "alter table tb_usuario" not in info:
            continue
        pid = row["Id"]
        print(f"  KILL ALTER {pid} (State={row.get('State')}, Time={row.get('Time')}s)")
        dal.update(f"KILL {pid}")
        mortos += 1
    return mortos


def matar_sessoes_antigas(dal, db_user: str, min_segundos: int = 30) -> int:
    meu_id = int(scalar(dal, "SELECT CONNECTION_ID() AS id", column="id"))
    df = dal.read("SHOW FULL PROCESSLIST")
    mortos = 0
    for _, row in df.iterrows():
        if row.get("User") != db_user:
            continue
        pid = int(row["Id"])
        if pid == meu_id:
            continue
        tempo = row.get("Time")
        try:
            t = int(tempo) if tempo is not None else 0
        except (TypeError, ValueError):
            t = 0
        if t >= min_segundos:
            print(f"  KILL sessao {pid} (Time={t}s, State={row.get('State')})")
            dal.update(f"KILL {pid}")
            mortos += 1
    return mortos


def aplicar_migracao(dal) -> None:
    if column_exists(dal, "tb_usuario", "id_empresa"):
        print("Colunas de vinculo ja existem — migracao nao necessaria.")
        return
    execute_sql_file(dal, SQL_PATH)


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--apenas-teste",
        action="store_true",
        help="Somente testa conexao e status, sem KILL nem ALTER",
    )
    args = parser.parse_args()

    print("=" * 60)
    print("Aplicar vinculos tb_usuario — RedMapa")
    print("=" * 60)

    try:
        dal = create_dal()
        db = database_name(dal)
        db_user = _db_user(dal)
        print(f"  Conexão: {dal.connection_string}")
        print(f"  Banco  : {db}")
        print("Conexao OK.")
    except Exception as exc:
        print(f"FALHA na conexao: {exc}")
        return 1

    try:
        info_df = dal.read("SELECT VERSION() AS v, USER() AS u")
        info = info_df.iloc[0]
        print(f"  {info['v']} | {info['u']}")

        for col in ("id_empresa", "id_turno", "id_local"):
            st = "EXISTE" if column_exists(dal, "tb_usuario", col) else "AUSENTE"
            print(f"  {col}: {st}")

        pl_df = dal.read("SHOW FULL PROCESSLIST")
        alters = pl_df[
            (pl_df["User"] == db_user)
            & pl_df["Info"].notna()
            & pl_df["Info"].astype(str).str.lower().str.contains("alter table tb_usuario")
        ]
        if not alters.empty:
            print(f"\nALTER TABLE pendentes do usuario {db_user}: {len(alters)}")
            for _, r in alters.iterrows():
                print(
                    f"  Id={r['Id']} State={r.get('State')} "
                    f"Time={r.get('Time')}s"
                )

        if args.apenas_teste:
            print("\nModo --apenas-teste: nenhuma alteracao feita.")
            return 0

        print(f"\nEncerrando sessoes antigas do usuario {db_user}...")
        n_sess = matar_sessoes_antigas(dal, db_user)
        print(f"  {n_sess} sessao(oes) encerrada(s).")

        if not alters.empty:
            print("\nEncerrando ALTER TABLE travados...")
            n_alt = matar_alters_travados(dal, db_user)
            print(f"  {n_alt} processo(s) encerrado(s).")

        time.sleep(2)

        print("\nAplicando migracao...")
        t0 = time.perf_counter()
        aplicar_migracao(dal)
        print(f"  OK em {time.perf_counter()-t0:.2f}s")

        print("\nVerificacao final:")
        for col in ("id_empresa", "id_turno", "id_local"):
            st = "EXISTE" if column_exists(dal, "tb_usuario", col) else "AUSENTE"
            print(f"  {col}: {st}")

        print("\nConcluido.")
        return 0
    except Exception as exc:
        print(f"\nERRO: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())

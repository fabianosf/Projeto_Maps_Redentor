# ----------------------------
# Deus seja Louvado!
# ----------------------------
"""Aplica schema_migrate_tb_map_plantao_time_postgresql.sql (TIMESTAMP → TIME)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

MIGRATE_FILE = ROOT / "database" / "schema_migrate_tb_map_plantao_time_postgresql.sql"


def _split_statements(sql: str) -> list[str]:
    lines: list[str] = []
    for line in sql.splitlines():
        stripped = line.strip()
        if stripped.startswith("--"):
            continue
        lines.append(line)
    blob = "\n".join(lines)
    return [p.strip() for p in blob.split(";") if p.strip()]


def main() -> int:
    from BackEnd.dal_factory import create_dal

    dal = create_dal()
    sgbd = str(getattr(dal, "sgbd", "") or "").lower()
    if "postgre" not in sgbd and sgbd != "postgresql":
        # Alguns DALs expõem via config
        try:
            from BackEnd.mapa_service import _dal_sgbd

            sgbd = _dal_sgbd(dal)
        except Exception:
            pass
    if sgbd != "postgresql":
        print(f"Pulando: migração específica de PostgreSQL (sgbd={sgbd!r}).")
        return 0

    sql = MIGRATE_FILE.read_text(encoding="utf-8")
    stmts = _split_statements(sql)
    print(f"Aplicando {len(stmts)} statement(s) de {MIGRATE_FILE.name}…")
    for i, stmt in enumerate(stmts, 1):
        print(f"  [{i}/{len(stmts)}] {stmt.splitlines()[0][:80]}…")
        ok = dal.execute_query(stmt, fetch=False)
        if ok is False:
            print(f"Falha no statement {i}. Abortando.")
            return 1
    cols = dal.read(
        """
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = 'tb_map'
          AND column_name IN ('inicio_jornada_des', 'fim_jornada_des')
        ORDER BY column_name
        """
    )
    if cols is None or getattr(cols, "empty", True):
        print("Não foi possível confirmar os tipos das colunas.")
        return 1
    print(cols.to_string(index=False))
    for _, row in cols.iterrows():
        if str(row["data_type"]).lower() != "time without time zone":
            print(f"Tipo inesperado em {row['column_name']}: {row['data_type']}")
            return 1
    print("OK.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

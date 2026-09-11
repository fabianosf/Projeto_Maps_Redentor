# ----------------------------
# Deus seja Louvado!
# ----------------------------
"""Aplica schema_migrate_tb_guia_disponibilidade_auditoria.sql via DAL."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

MIGRATE_FILE = ROOT / "database" / "schema_migrate_tb_guia_disponibilidade_auditoria.sql"


def _split_statements(sql: str) -> list[str]:
    lines: list[str] = []
    for line in sql.splitlines():
        if line.strip().startswith("--"):
            continue
        lines.append(line)
    parts: list[str] = []
    for part in "\n".join(lines).split(";"):
        stmt = part.strip()
        if stmt:
            parts.append(stmt)
    return parts


def main() -> int:
    from BackEnd.dal_factory import create_dal

    if not MIGRATE_FILE.is_file():
        print(f"Arquivo não encontrado: {MIGRATE_FILE}", file=sys.stderr)
        return 1

    statements = [
        s
        for s in _split_statements(MIGRATE_FILE.read_text(encoding="utf-8"))
        if not s.upper().startswith("USE ")
    ]
    dal = create_dal()
    print(f"Aplicando {MIGRATE_FILE.name} ({len(statements)} statements)...")
    with dal.transaction():
        for i, stmt in enumerate(statements, 1):
            preview = " ".join(stmt.split())[:100]
            upper = stmt.lstrip().upper()
            fetch = upper.startswith(("SELECT", "SHOW", "WITH"))
            try:
                dal.execute_query(stmt, fetch=fetch)
                print(f"  [{i}/{len(statements)}] OK — {preview}")
            except Exception as exc:  # noqa: BLE001
                print(f"  [{i}/{len(statements)}] FALHA — {preview}", file=sys.stderr)
                print(f"    {type(exc).__name__}: {exc}", file=sys.stderr)
                raise
    print("Migration OK.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

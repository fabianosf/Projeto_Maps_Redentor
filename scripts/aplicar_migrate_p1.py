# ----------------------------
# Deus seja Louvado!
# ----------------------------
"""Aplica migrations P1 frota + authz/auditoria (MariaDB, idempotente)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

FILES = [
    ROOT / "database" / "schema_migrate_frota_canonica_p1.sql",
    ROOT / "database" / "schema_migrate_mapa_authz_auditoria_p1.sql",
]


def _split_statements(sql: str) -> list[str]:
    lines: list[str] = []
    for line in sql.splitlines():
        stripped = line.strip()
        if stripped.startswith("--"):
            continue
        lines.append(line)
    parts: list[str] = []
    for part in "\n".join(lines).split(";"):
        stmt = part.strip()
        if stmt and not stmt.upper().startswith("USE "):
            parts.append(stmt)
    return parts


def main() -> int:
    from BackEnd.dal_factory import create_dal

    dal = create_dal()
    for path in FILES:
        if not path.is_file():
            print(f"Arquivo não encontrado: {path}", file=sys.stderr)
            return 1
        statements = _split_statements(path.read_text(encoding="utf-8"))
        print(f"Aplicando {path.name} ({len(statements)} statements)...")
        with dal.transaction():
            for i, stmt in enumerate(statements, 1):
                preview = " ".join(stmt.split())[:100]
                try:
                    upper = stmt.lstrip().upper()
                    fetch = upper.startswith(("SELECT", "SHOW", "WITH"))
                    dal.execute_query(stmt, fetch=fetch)
                    print(f"  [{i}/{len(statements)}] OK — {preview}")
                except Exception as exc:  # noqa: BLE001
                    print(f"  [{i}/{len(statements)}] FALHA — {preview}", file=sys.stderr)
                    print(f"    {type(exc).__name__}: {exc}", file=sys.stderr)
                    raise
        print(f"Migration OK: {path.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

# ----------------------------
# Deus seja Louvado!
# ----------------------------
"""Aplica migrations PostgreSQL via DAL (REDMAPA_SGBD=postgresql). Idempotente."""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

FILES = [
    ROOT / "database" / "schema_migrate_tb_configuracao_chave_valor_p2_postgresql.sql",
    ROOT / "database" / "schema_migrate_tb_mapa_codigo_empresa_postgresql.sql",
    ROOT / "database" / "schema_migrate_tb_map_plantao_time_postgresql.sql",
    ROOT / "database" / "schema_migrate_tb_item_map_ocupacao_completa_postgresql.sql",
    ROOT / "database" / "schema_migrate_mapa_authz_auditoria_p1_postgresql.sql",
    ROOT / "database" / "schema_migrate_frota_canonica_p1_postgresql.sql",
]


def _split_statements(sql: str) -> list[str]:
    lines: list[str] = []
    for line in sql.splitlines():
        if line.strip().startswith("--"):
            continue
        lines.append(line)
    parts: list[str] = []
    for part in "\n".join(lines).split(";"):
        stmt = part.strip()
        if stmt and not stmt.upper().startswith("USE "):
            parts.append(stmt)
    return parts


def _ignorable(exc: BaseException) -> bool:
    msg = str(exc).lower()
    return "already exists" in msg or "duplicate_object" in msg or "já existe" in msg


def main() -> int:
    os.environ.setdefault("REDMAPA_SGBD", "postgresql")
    os.environ.setdefault("REDMAPA_CONFIG", "map_PostGree")

    sgbd = (os.getenv("REDMAPA_SGBD") or "").strip().lower()
    if sgbd not in ("postgresql", "postgres", "postgree"):
        print(
            f"REDMAPA_SGBD={sgbd!r} — este script só aplica migrations PostgreSQL. "
            "Não há fallback para MariaDB.",
            file=sys.stderr,
        )
        return 2

    from BackEnd.dal_factory import create_dal

    dal = create_dal(config_arquivo=os.getenv("REDMAPA_CONFIG", "map_PostGree"), sgbd="postgresql")
    for path in FILES:
        if not path.is_file():
            print(f"Arquivo não encontrado: {path}", file=sys.stderr)
            return 1
        statements = _split_statements(path.read_text(encoding="utf-8"))
        print(f"Aplicando {path.name} ({len(statements)} statements)...")
        for i, stmt in enumerate(statements, 1):
            preview = " ".join(stmt.split())[:100]
            try:
                with dal.transaction():
                    upper = stmt.lstrip().upper()
                    fetch = upper.startswith(("SELECT", "SHOW", "WITH"))
                    dal.execute_query(stmt, fetch=fetch)
                print(f"  [{i}/{len(statements)}] OK — {preview}")
            except Exception as exc:  # noqa: BLE001
                if _ignorable(exc):
                    print(f"  [{i}/{len(statements)}] SKIP — {preview}")
                    continue
                print(f"  [{i}/{len(statements)}] FALHA — {preview}", file=sys.stderr)
                print(f"    {type(exc).__name__}: {exc}", file=sys.stderr)
                return 1
        print(f"Migration OK: {path.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

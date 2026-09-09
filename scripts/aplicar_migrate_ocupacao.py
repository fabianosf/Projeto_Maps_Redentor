# ----------------------------
# Deus seja Louvado!
# ----------------------------
"""Aplica migration de ocupação via DAL do projeto (map.dat). Idempotente."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

MIGRATE_FILE = ROOT / "database" / "schema_migrate_tb_item_map_ocupacao_completa.sql"


def _split_statements(sql: str) -> list[str]:
    """Remove comentários de linha e separa por ';'."""
    lines: list[str] = []
    for line in sql.splitlines():
        stripped = line.strip()
        if stripped.startswith("--"):
            continue
        lines.append(line)
    blob = "\n".join(lines)
    parts: list[str] = []
    for part in blob.split(";"):
        stmt = part.strip()
        if stmt:
            parts.append(stmt)
    return parts


def main() -> int:
    from BackEnd.dal_factory import create_dal

    if not MIGRATE_FILE.is_file():
        print(f"Arquivo não encontrado: {MIGRATE_FILE}", file=sys.stderr)
        return 1

    sql = MIGRATE_FILE.read_text(encoding="utf-8")
    statements = [s for s in _split_statements(sql) if not s.upper().startswith("USE ")]

    # Instância dedicada (não usa singleton da app)
    dal = create_dal()
    print(f"Aplicando {MIGRATE_FILE.name} ({len(statements)} statements)...")

    # Mesma conexão: variáveis @c/@s e PREPARE precisam permanecer na sessão
    with dal.transaction():
        for i, stmt in enumerate(statements, 1):
            preview = " ".join(stmt.split())[:100]
            try:
                upper = stmt.lstrip().upper()
                fetch = upper.startswith(("SELECT", "SHOW", "WITH"))
                dal.execute_query(stmt, fetch=fetch)
                print(f"  [{i}/{len(statements)}] OK — {preview}")
            except Exception as exc:  # noqa: BLE001
                print(f"  [{i}/{len(statements)}] FALHA — {preview}")
                print(f"    {type(exc).__name__}: {exc}", file=sys.stderr)
                raise

    df = dal.read(
        """
        SELECT COLUMN_NAME
        FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = 'tb_item_map'
          AND COLUMN_NAME IN (
            'status_escala','data_baixa','hora_baixa','motivo_baixa',
            'observacao_baixa','inicio_real','fim_real','duracao_trabalhada_minutos'
          )
        ORDER BY COLUMN_NAME
        """
    )
    cols = sorted(str(x) for x in df["COLUMN_NAME"].tolist()) if not df.empty else []
    print("Colunas presentes:", ", ".join(cols) if cols else "(nenhuma)")
    required = {
        "status_escala",
        "data_baixa",
        "hora_baixa",
        "motivo_baixa",
        "observacao_baixa",
        "inicio_real",
        "fim_real",
        "duracao_trabalhada_minutos",
    }
    missing = sorted(required - set(cols))
    if missing:
        print("FALTANDO:", ", ".join(missing), file=sys.stderr)
        return 1
    print("Migration OK.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

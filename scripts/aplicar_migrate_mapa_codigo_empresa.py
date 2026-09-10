# ----------------------------
# Deus seja Louvado!
# ----------------------------
"""Aplica schema_migrate_tb_mapa_codigo_empresa.sql via DAL + backfill de códigos."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

MIGRATE_FILE = ROOT / "database" / "schema_migrate_tb_mapa_codigo_empresa.sql"


def _split_statements(sql: str) -> list[str]:
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


def _format_codigo(prefixo: str, seq: int) -> str:
    n = int(seq)
    width = max(2, len(str(n)))
    return f"{prefixo.strip()}{n:0{width}d}"


def _parse_seq(codigo: str, prefixo: str) -> int | None:
    c = str(codigo or "").strip()
    p = str(prefixo or "").strip()
    if not c or not p:
        return None
    if not c.lower().startswith(p.lower()):
        return None
    suf = c[len(p) :]
    if not suf.isdigit():
        return None
    return int(suf)


def _backfill_codigos(dal) -> None:
    empresas = dal.read(
        """
        SELECT id_empresa, prefixo_mapa
        FROM tb_empresa
        WHERE ativo = 1
          AND prefixo_mapa IS NOT NULL
          AND TRIM(prefixo_mapa) <> ''
        ORDER BY id_empresa
        """
    )
    if empresas is None or empresas.empty:
        print("Backfill: nenhuma empresa com prefixo_mapa.")
        return

    for _, emp in empresas.iterrows():
        id_emp = int(emp["id_empresa"])
        prefixo = str(emp["prefixo_mapa"]).strip()

        existentes = dal.read(
            """
            SELECT id_registro, cod_map, codigo_mapa
            FROM tb_map
            WHERE id_empresa = ?
            ORDER BY cod_map ASC, id_registro ASC
            """,
            (id_emp,),
        )
        max_seq = 0
        pendentes: list[tuple[int, int]] = []
        if existentes is not None and not existentes.empty:
            for _, row in existentes.iterrows():
                cod = row.get("codigo_mapa")
                parsed = _parse_seq(str(cod) if cod is not None else "", prefixo)
                if parsed is not None:
                    max_seq = max(max_seq, parsed)
                else:
                    pendentes.append((int(row["id_registro"]), int(row["cod_map"])))

        for id_reg, _cod_map in pendentes:
            max_seq += 1
            codigo = _format_codigo(prefixo, max_seq)
            ok = dal.update(
                "UPDATE tb_map SET codigo_mapa = ? WHERE id_registro = ? AND codigo_mapa IS NULL",
                (codigo, id_reg),
            )
            if not ok:
                # colisão: tenta próximo
                while True:
                    max_seq += 1
                    codigo = _format_codigo(prefixo, max_seq)
                    ok2 = dal.update(
                        "UPDATE tb_map SET codigo_mapa = ? WHERE id_registro = ? AND codigo_mapa IS NULL",
                        (codigo, id_reg),
                    )
                    if ok2:
                        break
                    if max_seq > 99999:
                        raise RuntimeError(f"Falha ao backfill mapa {id_reg}")

        seq_row = dal.read(
            "SELECT ultimo_seq FROM tb_mapa_seq WHERE id_empresa = ?",
            (id_emp,),
        )
        if seq_row is None or seq_row.empty:
            dal.create(
                "INSERT INTO tb_mapa_seq (id_empresa, ultimo_seq) VALUES (?, ?)",
                (id_emp, max_seq),
            )
        else:
            atual = int(seq_row.iloc[0]["ultimo_seq"] or 0)
            if max_seq > atual:
                dal.update(
                    "UPDATE tb_mapa_seq SET ultimo_seq = ? WHERE id_empresa = ?",
                    (max_seq, id_emp),
                )
        print(f"  empresa {id_emp} ({prefixo}): ultimo_seq={max_seq}, backfill={len(pendentes)}")


def main() -> int:
    from BackEnd.dal_factory import create_dal

    if not MIGRATE_FILE.is_file():
        print(f"Arquivo não encontrado: {MIGRATE_FILE}", file=sys.stderr)
        return 1

    sql = MIGRATE_FILE.read_text(encoding="utf-8")
    statements = [s for s in _split_statements(sql) if not s.upper().startswith("USE ")]
    dal = create_dal()
    print(f"Aplicando {MIGRATE_FILE.name} ({len(statements)} statements)...")

    with dal.transaction():
        for i, stmt in enumerate(statements, 1):
            preview = " ".join(stmt.split())[:110]
            upper = stmt.lstrip().upper()
            fetch = upper.startswith(("SELECT", "SHOW", "WITH", "SET @"))
            # SET @var := (SELECT ...) precisa execute; SET @sql := IF também
            if upper.startswith("SET "):
                fetch = False
            try:
                dal.execute_query(stmt, fetch=fetch)
                print(f"  [{i}/{len(statements)}] OK — {preview}")
            except Exception as exc:  # noqa: BLE001
                print(f"  [{i}/{len(statements)}] FALHA — {preview}", file=sys.stderr)
                print(f"    {type(exc).__name__}: {exc}", file=sys.stderr)
                raise

        print("Backfill codigo_mapa / tb_mapa_seq...")
        _backfill_codigos(dal)

    emp = dal.read(
        "SELECT id_empresa, descricao, prefixo_mapa FROM tb_empresa WHERE ativo = 1 ORDER BY id_empresa"
    )
    print("Empresas:", emp.to_dict(orient="records") if emp is not None and not emp.empty else [])
    cols = dal.read(
        """
        SELECT COLUMN_NAME AS c
        FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = 'tb_map'
          AND COLUMN_NAME IN ('codigo_mapa', 'id_empresa')
        """
    )
    print(
        "Colunas tb_map:",
        sorted(str(x) for x in cols["c"].tolist()) if cols is not None and not cols.empty else [],
    )
    print("Migration OK.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

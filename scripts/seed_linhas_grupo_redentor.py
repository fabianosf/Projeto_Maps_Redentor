# -*- coding: utf-8 -*-
"""Popular/atualizar tb_linha a partir de database/linhas_grupo_redentor.csv.

Regra: um registro por (id_empresa, codigo_linha).
Numero_Linha "600 / SN600" → 600; "844 / 861 / …" → vários números.
Itinerário → descricao (NOT NULL); não é exibido no form de MAPA.
"""

from __future__ import annotations

import csv
import os
import re
import sys
from collections import defaultdict
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR / "scripts"))

from dal_util import create_dal  # noqa: E402

CSV_PATH = BASE_DIR / "database" / "linhas_grupo_redentor.csv"

EMPRESA_CSV = {
    "viação redentor": "Redentor",
    "viacao redentor": "Redentor",
    "transportes futuro": "Futuro",
    "transportes barra": "Barra",
}


def _extract_numeros(numero_linha: str) -> list[int]:
    seen: set[int] = set()
    out: list[int] = []
    for part in str(numero_linha).split("/"):
        m = re.search(r"(\d+)", part.strip())
        if not m:
            continue
        n = int(m.group(1))
        if n <= 0 or n in seen:
            continue
        seen.add(n)
        out.append(n)
    return out


def _locais_padrao(dal) -> tuple[int, int]:
    df = dal.read(
        "SELECT id_local, codigo_local FROM tb_local WHERE ativo = 1 ORDER BY codigo_local"
    )
    if df.empty or len(df) < 1:
        raise RuntimeError("tb_local vazia — sem origem/destino padrão")
    ids = [int(r["id_local"]) for _, r in df.iterrows()]
    origem = ids[0]
    destino = ids[1] if len(ids) > 1 else ids[0]
    return origem, destino


def _id_empresa(dal, descricao: str) -> int:
    df = dal.read(
        """
        SELECT id_empresa FROM tb_empresa
        WHERE LOWER(TRIM(descricao)) = LOWER(?) AND ativo = 1
        """,
        (descricao,),
    )
    if df.empty:
        raise RuntimeError(f"Empresa não encontrada: {descricao}")
    return int(df.iloc[0]["id_empresa"])


def main() -> int:
    if not CSV_PATH.is_file():
        print(f"CSV não encontrado: {CSV_PATH}")
        return 1

    dal = create_dal()
    if not dal.test_connection():
        print("Falha de conexão")
        return 1

    id_origem, id_destino = _locais_padrao(dal)
    emp_ids = {
        "Redentor": _id_empresa(dal, "Redentor"),
        "Futuro": _id_empresa(dal, "Futuro"),
        "Barra": _id_empresa(dal, "Barra"),
    }

    # (id_empresa, codigo) -> descricao (primeiro itinerário visto)
    pares: dict[tuple[int, int], str] = {}
    with CSV_PATH.open(encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            emp_raw = (row.get("Empresa") or "").strip()
            emp_nome = EMPRESA_CSV.get(emp_raw.lower())
            if emp_nome is None:
                print(f"Empresa CSV ignorada: {emp_raw!r}")
                continue
            id_emp = emp_ids[emp_nome]
            itinerario = (row.get("Itinerario") or "").strip() or "Linha"
            if len(itinerario) > 150:
                itinerario = itinerario[:147] + "..."
            for codigo in _extract_numeros(row.get("Numero_Linha") or ""):
                key = (id_emp, codigo)
                if key not in pares:
                    pares[key] = itinerario

    inserted = updated = 0
    keep_keys = set(pares.keys())

    for (id_emp, codigo), descricao in sorted(pares.items(), key=lambda x: (x[0][0], x[0][1])):
        existe = dal.read(
            """
            SELECT id_linha FROM tb_linha
            WHERE id_empresa = ? AND codigo_linha = ?
            """,
            (id_emp, codigo),
        )
        if not existe.empty:
            id_linha = int(existe.iloc[0]["id_linha"])
            ok = dal.update(
                """
                UPDATE tb_linha
                SET descricao = ?, id_local_origem = ?, id_local_destino = ?, ativo = 1
                WHERE id_linha = ?
                """,
                (descricao, id_origem, id_destino, id_linha),
            )
            if ok:
                updated += 1
            else:
                print(f"Falha UPDATE empresa={id_emp} codigo={codigo}")
        else:
            ok = dal.create(
                """
                INSERT INTO tb_linha (
                    codigo_linha, id_empresa, descricao,
                    id_local_origem, id_local_destino, ativo
                ) VALUES (?, ?, ?, ?, ?, 1)
                """,
                (codigo, id_emp, descricao, id_origem, id_destino),
            )
            if ok:
                inserted += 1
            else:
                print(f"Falha INSERT empresa={id_emp} codigo={codigo}")

    # Desativa linhas ativas que não estão no CSV (ex.: seed demo 1..5)
    ativas = dal.read(
        "SELECT id_linha, id_empresa, codigo_linha FROM tb_linha WHERE ativo = 1"
    )
    desativadas = 0
    for _, row in ativas.iterrows():
        key = (int(row["id_empresa"]), int(row["codigo_linha"]))
        if key in keep_keys:
            continue
        if dal.update(
            "UPDATE tb_linha SET ativo = 0 WHERE id_linha = ?",
            (int(row["id_linha"]),),
        ):
            desativadas += 1

    por = dal.read(
        """
        SELECT e.descricao, COUNT(*) AS n
        FROM tb_linha l
        INNER JOIN tb_empresa e ON e.id_empresa = l.id_empresa
        WHERE l.ativo = 1
        GROUP BY e.descricao
        ORDER BY e.descricao
        """
    )
    print(f"pares CSV={len(pares)} insert={inserted} update={updated} desativadas={desativadas}")
    print(por.to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

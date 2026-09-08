# -*- coding: utf-8 -*-
"""Aplica schema_migrate_tb_veiculo_id_empresa_mariadb.sql via DAL."""

from __future__ import annotations

import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE, "scripts"))

from dal_util import create_dal  # noqa: E402


def _count(dal, sql: str, params: tuple) -> int:
    return int(dal.read(sql, params).iloc[0]["n"])


def main() -> int:
    dal = create_dal()
    if not dal.test_connection():
        print("Falha de conexão")
        return 1

    has_col = _count(
        dal,
        """
        SELECT COUNT(*) AS n FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = ? AND TABLE_NAME = ? AND COLUMN_NAME = ?
        """,
        ("map", "tb_veiculo", "id_empresa"),
    )
    if has_col == 0:
        ok = dal.create(
            """
            ALTER TABLE tb_veiculo
            ADD COLUMN id_empresa INT NULL
                COMMENT 'FK tb_empresa.id_empresa'
                AFTER ativo
            """
        )
        print("ADD COLUMN id_empresa:", ok)
    else:
        print("COLUMN id_empresa: já existe")

    has_idx = _count(
        dal,
        """
        SELECT COUNT(*) AS n FROM information_schema.STATISTICS
        WHERE TABLE_SCHEMA = ? AND TABLE_NAME = ? AND INDEX_NAME = ?
        """,
        ("map", "tb_veiculo", "idx_tb_veiculo_id_empresa"),
    )
    if has_idx == 0:
        ok = dal.create(
            "ALTER TABLE tb_veiculo ADD KEY idx_tb_veiculo_id_empresa (id_empresa)"
        )
        print("ADD INDEX:", ok)
    else:
        print("INDEX idx_tb_veiculo_id_empresa: já existe")

    has_fk = _count(
        dal,
        """
        SELECT COUNT(*) AS n FROM information_schema.TABLE_CONSTRAINTS
        WHERE TABLE_SCHEMA = ? AND TABLE_NAME = ?
          AND CONSTRAINT_NAME = ? AND CONSTRAINT_TYPE = ?
        """,
        ("map", "tb_veiculo", "fk_tb_veiculo_empresa", "FOREIGN KEY"),
    )
    if has_fk == 0:
        ok = dal.create(
            """
            ALTER TABLE tb_veiculo
            ADD CONSTRAINT fk_tb_veiculo_empresa
                FOREIGN KEY (id_empresa) REFERENCES tb_empresa (id_empresa)
            """
        )
        print("ADD FK:", ok)
    else:
        print("FK fk_tb_veiculo_empresa: já existe")

    # Popular por faixa (origem razoável); sem match → NULL
    faixas = (
        ("Futuro", 30000, 30999),
        ("Redentor", 40000, 40999),
        ("Barra", 13000, 13999),
    )
    for desc, lo, hi in faixas:
        ok = dal.update(
            """
            UPDATE tb_veiculo v
            INNER JOIN tb_empresa e ON e.descricao = ? AND e.ativo = 1
            SET v.id_empresa = e.id_empresa
            WHERE v.id_empresa IS NULL
              AND v.codigo_veiculo BETWEEN ? AND ?
            """,
            (desc, lo, hi),
        )
        print(f"UPDATE faixa {desc} [{lo}-{hi}]:", ok)

    rows = dal.read(
        """
        SELECT id_veiculo, numero_frota, codigo_veiculo, id_empresa
        FROM tb_veiculo
        ORDER BY id_veiculo
        """
    )
    print(rows.to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

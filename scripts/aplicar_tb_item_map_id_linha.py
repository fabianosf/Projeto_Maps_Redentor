"""Aplica migration tb_item_map.id_linha no MariaDB (idempotente parcial)."""
from __future__ import annotations

from BackEnd.dal_factory import get_dal_instance


def _col_exists(dal, table: str, col: str) -> bool:
    df = dal.read(
        "SELECT COUNT(*) AS c FROM information_schema.columns "
        "WHERE table_schema = DATABASE() AND table_name = ? AND column_name = ?",
        (table, col),
    )
    return not df.empty and int(df.iloc[0]["c"]) > 0


def main() -> None:
    dal = get_dal_instance()
    if not dal.test_connection():
        print("DB offline")
        return

    if not _col_exists(dal, "tb_item_map", "id_linha"):
        ok = dal.create(
            "ALTER TABLE tb_item_map ADD COLUMN id_linha INT NULL "
            "COMMENT 'FK tb_linha' AFTER idmap",
            None,
        )
        print("add_column", ok)
    else:
        print("column_exists")

    ok_bf = dal.update(
        """
        UPDATE tb_item_map i
        INNER JOIN tb_map m ON m.id_registro = i.idmap
        SET i.id_linha = m.id_linha
        WHERE i.id_linha IS NULL AND m.id_linha IS NOT NULL
        """,
        None,
    )
    print("backfill", ok_bf)

    nulls = dal.read("SELECT COUNT(*) AS c FROM tb_item_map WHERE id_linha IS NULL")
    print("itens_sem_linha", 0 if nulls.empty else int(nulls.iloc[0]["c"]))

    # FK / NOT NULL — best effort
    try:
        dal.create(
            "ALTER TABLE tb_item_map ADD KEY idx_tb_item_map_id_linha (id_linha)",
            None,
        )
    except Exception as exc:
        print("idx_skip", exc)
    try:
        dal.create(
            "ALTER TABLE tb_item_map ADD CONSTRAINT fk_tb_item_map_linha "
            "FOREIGN KEY (id_linha) REFERENCES tb_linha (id_linha)",
            None,
        )
    except Exception as exc:
        print("fk_skip", exc)

    n = 0 if nulls.empty else int(nulls.iloc[0]["c"])
    if n == 0:
        ok_nn = dal.create(
            "ALTER TABLE tb_item_map MODIFY id_linha INT NOT NULL "
            "COMMENT 'FK tb_linha — empresa via linha'",
            None,
        )
        print("not_null", ok_nn)
    else:
        print("skip_not_null_due_to_nulls", n)

    ok_map = dal.create(
        "ALTER TABLE tb_map MODIFY id_linha INT NULL "
        "COMMENT 'Legado — preferir tb_item_map.id_linha'",
        None,
    )
    print("map_nullable", ok_map)

    c1 = dal.read("SELECT COUNT(*) AS c FROM tb_map")
    c2 = dal.read("SELECT COUNT(*) AS c FROM tb_item_map")
    print("maps", 0 if c1.empty else int(c1.iloc[0]["c"]))
    print("itens", 0 if c2.empty else int(c2.iloc[0]["c"]))


if __name__ == "__main__":
    main()

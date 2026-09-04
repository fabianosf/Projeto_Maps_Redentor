"""Verifica estrutura e dados no DB para telas de viagens."""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from dal_util import ScriptDal, create_dal

dal = create_dal()
cur = ScriptDal(dal)

for tabela in ("tb_map", "tb_item_map", "tb_viagem"):
    cur.execute(f"DESCRIBE {tabela}")
    cols = [r["Field"] for r in cur.fetchall()]
    print(f"{tabela}: {cols}")

cur.execute("SELECT * FROM tb_map ORDER BY 1 LIMIT 5")
print("tb_map:", cur.fetchall())

cur.execute("SELECT * FROM tb_item_map ORDER BY 1 LIMIT 5")
print("tb_item_map:", cur.fetchall())

cur.execute("SELECT * FROM tb_viagem ORDER BY 1 LIMIT 5")
print("tb_viagem:", cur.fetchall())

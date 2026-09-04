# -*- coding: utf-8 -*-
from __future__ import annotations

import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from dal_util import ScriptDal, create_dal, database_name

dal = create_dal()
db = database_name(dal)
cur = ScriptDal(dal)

queries = [
    "SHOW TABLES LIKE 'tb_usuario'",
    f"SELECT COUNT(*) AS n FROM information_schema.COLUMNS WHERE TABLE_SCHEMA='{db}' AND TABLE_NAME='tb_usuario'",
    f"SELECT COLUMN_NAME FROM information_schema.COLUMNS WHERE TABLE_SCHEMA='{db}' AND TABLE_NAME='tb_usuario' AND COLUMN_NAME IN ('id_empresa','id_turno','id_local')",
    "SELECT COUNT(*) AS n FROM tb_usuario",
]
for sql in queries:
    t = time.time()
    try:
        cur.execute(sql)
        print(f"OK  {time.time()-t:.2f}s | {sql[:70]}")
        print(f"    -> {cur.fetchall()}")
    except Exception as e:
        print(f"ERR {time.time()-t:.2f}s | {sql[:70]}")
        print(f"    -> {e}")

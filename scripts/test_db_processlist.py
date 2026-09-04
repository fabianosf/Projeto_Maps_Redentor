# -*- coding: utf-8 -*-
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from dal_util import create_dal

dal = create_dal()
df = dal.read("SHOW FULL PROCESSLIST")
print(f"Processos ativos: {len(df)}")
for _, r in df.iterrows():
    info = str(r.get("Info") or "")[:80]
    print(f"  Id={r['Id']} User={r['User']} State={r.get('State')} Time={r.get('Time')}s")
    if info:
        print(f"       SQL: {info}")

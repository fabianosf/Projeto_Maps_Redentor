#!/usr/bin/env python3
"""Ponte DAL.py -> VB.NET ClDAL. Uso: echo SQL | py -3 dal_bridge.py read"""
from __future__ import annotations
import json, os, sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (BASE, os.path.join(BASE, "LOG")):
    if p not in sys.path:
        sys.path.insert(0, p)

from dal_factory import get_dal_instance


def main() -> int:
    if len(sys.argv) < 2:
        print(json.dumps({"ok": False, "error": "Comando: read|create|update|delete"}))
        return 1
    cmd = sys.argv[1].lower()
    sql = sys.stdin.read()
    if not sql.strip():
        print(json.dumps({"ok": False, "error": "SQL vazio"}))
        return 1
    dal = get_dal_instance()
    try:
        if cmd == "read":
            df = dal.read(sql)
            print(json.dumps({
                "ok": True,
                "columns": list(df.columns),
                "rows": df.to_dict(orient="records"),
            }, default=str))
        elif cmd == "create":
            print(json.dumps({"ok": bool(dal.create(sql))}))
        elif cmd == "update":
            print(json.dumps({"ok": bool(dal.update(sql))}))
        elif cmd == "delete":
            print(json.dumps({"ok": bool(dal.delete(sql))}))
        else:
            print(json.dumps({"ok": False, "error": f"Comando inválido: {cmd}"}))
            return 1
        return 0
    except Exception as exc:
        print(json.dumps({"ok": False, "error": str(exc)}))
        return 1


if __name__ == "__main__":
    sys.exit(main())

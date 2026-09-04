#!/usr/bin/env python3
"""Testa DAL + banco crip (executar na raiz PROJ_ONIX ou PROJ_MAP)."""
from __future__ import annotations
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from dal_factory import get_dal_instance


def main() -> int:
    dal = get_dal_instance()
    print("connection:", dal.connection_string)
    if not dal.test_connection():
        print("FALHA: test_connection")
        return 1
    df = dal.read("SELECT chave, valor FROM tb_conf")
    print(df.to_string(index=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())

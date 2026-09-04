#!/usr/bin/env python3
"""Gera crip.dat em DAL/arquivos_crip/arq/ (mesmo servidor map, banco crip)."""
from __future__ import annotations
import json, os, sys
from cryptography.fernet import Fernet

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CRIP = os.path.join(BASE, "DAL", "arquivos_crip")
CHAVE = os.path.join(CRIP, "chave", "chave.key")
ARQ = os.path.join(CRIP, "arq", "crip.dat")

DADOS = {
    "sgbd": "mariadb",
    "servidor": "10.1.1.29",
    "porta": "3306",
    "usuario": "alberto",
    "senha": "at5001",
    "bd": "crip",
}


def main() -> int:
    if not os.path.exists(CHAVE):
        print(f"ERRO: chave não encontrada: {CHAVE}")
        return 1
    with open(CHAVE, "rb") as f:
        chave = f.read()
    os.makedirs(os.path.dirname(ARQ), exist_ok=True)
    cipher = Fernet(chave)
    blob = cipher.encrypt(json.dumps(DADOS, indent=4, ensure_ascii=False).encode("utf-8"))
    with open(ARQ, "w", encoding="utf-8") as f:
        f.write(blob.decode("utf-8"))
    print(f"Gerado: {ARQ}")
    return 0

if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""
Gera arquivos de configuração criptografados map.dat e map_PostGree.dat
em DAL/arquivos_crip/arq/ (Fernet + DAL/arquivos_crip/chave/chave.key).

Padrão PROJ_PAD: chave em arquivos_crip/chave/, .dat em arquivos_crip/arq/.
"""

from __future__ import annotations

import json
import os
import sys

from cryptography.fernet import Fernet

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARQUIVOS_CRIP_DIR = os.path.join(BASE_DIR, "DAL", "arquivos_crip")
CHAVE_DIR = os.path.join(ARQUIVOS_CRIP_DIR, "chave")
ARQ_DIR = os.path.join(ARQUIVOS_CRIP_DIR, "arq")
KEY_PATH = os.path.join(CHAVE_DIR, "chave.key")

CONFIGS = {
    # Parametros.png — servidor MariaDB da rede (RedMapa / banco map)
    "map.dat": {
        "sgbd": "mariadb",
        "servidor": "10.1.1.29",
        "porta": "3306",
        "usuario": "alberto",
        "senha": "at5001",
        "bd": "map",
    },

    "map_PostGree.dat": {
        "sgbd": "postgresql",
        "servidor": "localhost",
        "porta": "5432",
        "usuario": "postgres",
        "senha": "postgres",
        "bd": "map",
    },

    # PROJ_ONIX — banco crip (MariaDB rede)
    "crip.dat": {
        "sgbd": "mariadb",
        "servidor": "10.1.1.29",
        "porta": "3306",
        "usuario": "alberto",
        "senha": "at5001",
        "bd": "crip",
    },
}


def _carregar_ou_criar_chave() -> bytes:
    os.makedirs(CHAVE_DIR, exist_ok=True)
    os.makedirs(ARQ_DIR, exist_ok=True)
    if os.path.exists(KEY_PATH):
        with open(KEY_PATH, "rb") as f:
            chave = f.read()
        if chave:
            return chave
    chave = Fernet.generate_key()
    with open(KEY_PATH, "wb") as f:
        f.write(chave)
    print(f"Chave criada: {KEY_PATH}")
    return chave


def _gerar_arquivo(nome: str, dados: dict, chave: bytes) -> str:
    cipher = Fernet(chave)
    json_texto = json.dumps(dados, indent=4, ensure_ascii=False)
    criptografado = cipher.encrypt(json_texto.encode("utf-8")).decode("utf-8")
    caminho = os.path.join(ARQ_DIR, nome)
    with open(caminho, "w", encoding="utf-8") as f:
        f.write(criptografado)
    return caminho


def main() -> int:
    chave = _carregar_ou_criar_chave()
    for nome, dados in CONFIGS.items():
        caminho = _gerar_arquivo(nome, dados, chave)
        print(f"Gerado: {caminho}")
    print("\nAjuste usuario/senha nos .dat conforme seu ambiente local.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

# -*- coding: utf-8 -*-
"""
Atualiza Doc_Proj_Map.odt — arquitetura com cadastro de usuários na própria aplicação:
  - Substitui imagem do diagrama
  - Corrige textos que citam aplicação externa de cadastro
"""

from __future__ import annotations

import re
import shutil
import zipfile
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
ODT_PATH = BASE / "Doc" / "Doc_Proj_Map.odt"
BACKUP_PATH = BASE / "Doc" / "Doc_Proj_Map.odt.bak"
ARCH_IMAGE_SRC = BASE / "Doc" / "images" / "redmapa-arquitetura.png"
ARCH_IMAGE_ODT = "Pictures/1000000000000600000004004045EB80.png"

REPLACEMENTS: list[tuple[str, str]] = [
    (
        "Pré-cadastro de usuários (aplicação externa)",
        "Cadastro de usuários (RedMapa — Admin)",
    ),
    (
        "Usuários não se auto-cadastram no RedMapa. Cadastro feito por aplicação externa "
        "(RH/administração). App externa: INSERT em tb_usuario; senha inicial 12345; hash "
        "bcrypt em tb_usuario.senha; trocar_senha = 1.",
        "Cadastro na própria aplicação RedMapa — perfil Administrador, tela Configuração "
        "(RF-UI-020). BackEnd: INSERT em tb_usuario via API /api/v1; senha inicial 12345; "
        "hash bcrypt; trocar_senha = 1. Despachante não cadastra usuários.",
    ),
    (
        "Senha inicial definida pela aplicação externa",
        "Senha inicial no cadastro de usuários",
    ),
    (
        "Todo usuário externo recebe senha inicial 12345 (texto claro). Banco armazena hash "
        "bcrypt — nunca texto puro. RedMapa não altera no cadastro; apenas valida no 1º login.",
        "Todo usuário cadastrado pelo Administrador recebe senha inicial 12345 (texto claro). "
        "Banco armazena hash bcrypt via BackEnd RedMapa; validação no 1º login.",
    ),
    (
        "cadastro externo hasheia 12345",
        "cadastro Admin (RedMapa) hasheia 12345",
    ),
    (
        "Aplicação externa de cadastro e RedMapa usam o mesmo bcrypt (cost 12)",
        "Cadastro de usuários (RedMapa) e demais fluxos usam o mesmo bcrypt (cost 12)",
    ),
    (
        "substituindo a senha provisória definida no cadastro externo.",
        "substituindo a senha provisória definida no cadastro interno (Administrador).",
    ),
    (
        "Integração com cadastro externo: usuários são pré-cadastrados em tb_usuario por "
        "aplicação externa (SQL direto no banco), com senha inicial bcrypt; o RedMapa não "
        "expõe endpoint público de criação de usuário.",
        "Cadastro de usuários: realizado na própria aplicação RedMapa — perfil Administrador "
        "acessa a tela Configuração; BackEnd persiste em tb_usuario via API REST (/api/v1), "
        "com senha inicial bcrypt de 12345 e trocar_senha = 1.",
    ),
    (
        "Cadastro externo ↔ MariaDB",
        "Cadastro usuários (Admin) ↔ API RedMapa",
    ),
    (
        "SQL direto",
        "HTTPS/JSON",
    ),
    (
        "INSERT em tb_usuario (fora do RedMapa)",
        "INSERT em tb_usuario via BackEnd (bcrypt)",
    ),
    (
        "4.8 Sistemas externos",
        "4.8 Integrações e utilitários",
    ),
    (
        "Aplicação externa de cadastro",
        "Cadastro de usuários (RedMapa)",
    ),
    (
        "Pré-cadastra usuários em tb_usuario",
        "Administrador cadastra usuários em tb_usuario",
    ),
    (
        "SQL direto no banco; senha inicial bcrypt de 12345; não passa pela API RedMapa",
        "Tela Configuração → API /api/v1; senha inicial bcrypt de 12345; perfil Admin",
    ),
]


def patch_content_xml(xml: str) -> tuple[str, int]:
    count = 0
    for old, new in REPLACEMENTS:
        if old in xml:
            xml = xml.replace(old, new)
            count += 1
    return xml, count


def main() -> None:
    if not ODT_PATH.exists():
        raise FileNotFoundError(ODT_PATH)
    if not ARCH_IMAGE_SRC.exists():
        raise FileNotFoundError(
            f"Execute antes: python scripts/generate_redmapa_arquitetura_png.py ({ARCH_IMAGE_SRC})"
        )

    shutil.copy2(ODT_PATH, BACKUP_PATH)

    with zipfile.ZipFile(ODT_PATH, "r") as zin:
        content = zin.read("content.xml").decode("utf-8")
        entries = {item.filename: zin.read(item.filename) for item in zin.infolist()}

    new_content, n = patch_content_xml(content)
    if "aplicação externa de cadastro" in new_content.lower() or "cadastro externo" in new_content.lower():
        # fallback: remove bloco residual com regex leve
        new_content = re.sub(
            r"Aplicação externa de cadastro[^<]{0,200}RedMapa",
            "Cadastro de usuários na própria aplicação RedMapa",
            new_content,
            flags=re.IGNORECASE,
        )

    entries["content.xml"] = new_content.encode("utf-8")
    entries[ARCH_IMAGE_ODT] = ARCH_IMAGE_SRC.read_bytes()

    temp = ODT_PATH.with_suffix(".tmp.odt")
    with zipfile.ZipFile(temp, "w") as zout:
        for name, data in entries.items():
            zout.writestr(name, data)

    temp.replace(ODT_PATH)
    print(f"ODT atualizado: {ODT_PATH}")
    print(f"Imagem substituída: {ARCH_IMAGE_ODT}")
    print(f"Trechos de texto alterados: {n}")
    print(f"Backup: {BACKUP_PATH}")


if __name__ == "__main__":
    main()

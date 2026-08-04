# -*- coding: utf-8 -*-
"""
Padroniza Doc_Proj_Map.odt:
- React Native como FrontEnd
- Senha provisória 12345
- Configurações em DAL/arquivos_crip/ (sem conf/)
- Estrutura FrontEnd/ e BackEnd/ no repositório
"""

from __future__ import annotations

import copy
import re
import zipfile
from pathlib import Path

from odt_lib import BACKUP_PATH, ODT_PATH, NS, read_content_root, write_content_xml

NEW_TREE = """PROJ_MAP/
├── FrontEnd/                # FrontEnd React Native (Expo)
│   ├── App.tsx
│   └── src/                 # api, config, navigation, screens, utils
├── DAL/                     # Data Access Layer + arquivos_crip/
│   └── arquivos_crip/       # chave/ e arq/*.dat (Fernet)
├── database/                # DDL, seeds, migrações SQL
├── Doc/                     # Doc_Proj_Map.odt (documentação única)
├── BackEnd/                 # BackEnd Flask (/api/v1)
├── scripts/                 # Utilitários e odt_lib.py
└── requirements.txt"""

REPLACEMENTS = [
    (r"\b123456\b", "12345"),
    ("HTML, CSS, JavaScript", "React Native (Expo)"),
    ("HTML/CSS/JS", "React Native"),
    ("FrontEnd estático", "FrontEnd React Native"),
    ("frontend/", "FrontEnd/"),
    ("mobile/", "FrontEnd/"),
    ("python/", "BackEnd/"),
    ("├── conf/", "├── DAL/arquivos_crip/"),
    ("conf/chave.key", "DAL/arquivos_crip/chave/chave.key"),
    ("conf/*.dat", "DAL/arquivos_crip/arq/*.dat"),
    ("conf/map_PostGree.dat", "DAL/arquivos_crip/arq/map_PostGree.dat"),
    ("Doc/Relatorio_Plataforma_Vercel.md", "Doc_Proj_Map.odt"),
    ("aplicação externa", "Administrador (RedMapa)"),
    ("App externa", "Admin RedMapa"),
]


def patch_paragraphs() -> int:
    root = read_content_root()
    text_el = root.find(".//office:text", NS)
    if text_el is None:
        raise RuntimeError("office:text não encontrado")
    changed = 0
    for p in text_el.findall("text:p", NS):
        original = "".join(p.itertext())
        updated = original
        for old, new in REPLACEMENTS:
            if old.startswith(r"\b"):
                updated = re.sub(old, new, updated)
            else:
                updated = updated.replace(old, new)
        if "O FrontEnd está na pasta frontend/" in updated:
            updated = updated.replace(
                "O FrontEnd está na pasta frontend/",
                "O FrontEnd React Native está na pasta FrontEnd/",
            )
        if "pasta mobile/" in updated:
            updated = updated.replace("pasta mobile/", "pasta FrontEnd/")
        if updated != original:
            for c in list(p):
                p.remove(c)
            p.text = updated
            changed += 1

    children = list(text_el)
    for i, c in enumerate(children):
        if c.tag.endswith("p") and "".join(c.itertext()).strip().startswith("PROJ_MAP/"):
            tpl = c
            style = tpl.get("{urn:oasis:names:tc:opendocument:xmlns:text:1.0}style-name")
            end = i + 1
            while end < len(children):
                t = "".join(children[end].itertext()).strip()
                if children[end].tag.endswith("p") and t.startswith("requirements.txt"):
                    end += 1
                    break
                if children[end].tag.endswith("p") and t and not t.startswith("├") and not t.startswith("└") and "PROJ_MAP" not in t and "requirements" not in t:
                    break
                end += 1
            for j in range(end - 1, i - 1, -1):
                text_el.remove(children[j])
            for k, line in enumerate(NEW_TREE.split("\n")):
                np = copy.deepcopy(tpl)
                for ch in list(np):
                    np.remove(ch)
                np.text = line
                if style:
                    np.set("{urn:oasis:names:tc:opendocument:xmlns:text:1.0}style-name", style)
                text_el.insert(i + k, np)
            changed += 1
            break

    write_content_xml(root)
    return changed


def main() -> None:
    n = patch_paragraphs()
    print(f"Atualizado: {ODT_PATH}")
    print(f"Backup: {BACKUP_PATH}")
    print(f"Parágrafos alterados: {n}")


if __name__ == "__main__":
    main()

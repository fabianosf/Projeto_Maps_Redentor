# -*- coding: utf-8 -*-
"""Atualiza referências python/→BackEnd/ e mobile/→FrontEnd/ no Doc_Proj_Map.odt."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from odt_lib import NS, read_content_root, write_content_xml

REPLACEMENTS = [
    ("pasta mobile/", "pasta FrontEnd/"),
    ("├── mobile/", "├── FrontEnd/"),
    ("├── python/", "├── BackEnd/"),
    ("→ mobile/", "→ FrontEnd/"),
    ("→ python/", "→ BackEnd/"),
    ("FrontEnd → mobile/", "FrontEnd → FrontEnd/"),
    ("BackEnd → python/", "BackEnd → BackEnd/"),
    ("scaffold_mobile.py", "scaffold_frontend.py"),
    ("estrutura mobile/", "estrutura FrontEnd/"),
    ("python/app.py", "BackEnd/app.py"),
    ("python/auth_routes.py", "BackEnd/auth_routes.py"),
    ("python/auth_service.py", "BackEnd/auth_service.py"),
    ("python/session_store.py", "BackEnd/session_store.py"),
    ("python/auth_session.py", "BackEnd/auth_session.py"),
    ("python/DAL.py", "BackEnd/DAL.py"),
    ("python/CONF.py", "BackEnd/CONF.py"),
    ("python -m python.app", "python -m BackEnd.app"),
]


def main() -> None:
    root = read_content_root()
    text_el = root.find(".//office:text", NS)
    if text_el is None:
        raise RuntimeError("office:text não encontrado")

    changed = 0
    for p in text_el.findall("text:p", NS):
        original = "".join(p.itertext())
        updated = original
        for old, new in REPLACEMENTS:
            updated = updated.replace(old, new)
        if updated != original:
            for ch in list(p):
                p.remove(ch)
            p.text = updated
            changed += 1

    write_content_xml(root)
    print(f"Parágrafos atualizados: {changed}")


if __name__ == "__main__":
    main()

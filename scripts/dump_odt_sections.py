# -*- coding: utf-8 -*-
"""Exporta índice de seções do Doc_Proj_Map.odt para scripts/_sections_dump.txt."""

from pathlib import Path

from odt_lib import get_text_element, paragraph_texts, read_content_root

OUT = Path(__file__).resolve().parent / "_sections_dump.txt"


def main() -> None:
    root = read_content_root()
    text_el = get_text_element(root)
    children = list(text_el)
    lines = []
    for i, c in enumerate(children):
        if not c.tag.endswith("p"):
            continue
        style = c.get("{urn:oasis:names:tc:opendocument:xmlns:text:1.0}style-name", "")
        t = "".join(c.itertext()).strip().replace("\xa0", " ")
        if not t and i not in range(100, 250):
            continue
        if i < 250 or t[:2].replace(".", "").isdigit() or "Requisito" in t or "Projeto" in t or "Arquitetura" in t:
            lines.append(f"{i:4d} [{style}] {t[:120]}")
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Exportado: {OUT} ({len(lines)} linhas)")
    print(f"IDs documentados: {len(__import__('odt_lib').documented_ids(root))}")


if __name__ == "__main__":
    main()

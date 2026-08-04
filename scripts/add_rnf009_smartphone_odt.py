# -*- coding: utf-8 -*-
"""Insere RNF-009 (exibição FrontEnd em smartphone de referência) no Doc_Proj_Map.odt."""

from __future__ import annotations

import copy
import re
import shutil
import zipfile
from pathlib import Path
import xml.etree.ElementTree as ET

BASE = Path(__file__).resolve().parents[1]
ODT_PATH = BASE / "Doc" / "Doc_Proj_Map.odt"
BACKUP_PATH = BASE / "Doc" / "Doc_Proj_Map.odt.bak"

NS = {
    "office": "urn:oasis:names:tc:opendocument:xmlns:office:1.0",
    "text": "urn:oasis:names:tc:opendocument:xmlns:text:1.0",
    "table": "urn:oasis:names:tc:opendocument:xmlns:table:1.0",
}

RNF_009 = {
    "titulo_curto": "Exibição em smartphone de referência",
    "descricao": (
        "Todas as telas do FrontEnd (Login, MAPA e demais interfaces gráficas) devem ser "
        "projetadas, implementadas e validadas para exibição em smartphone, conforme "
        "dispositivo de referência documentado no Anexo 10 — Samsung Galaxy A03 Core "
        "(SM-A032F): Android 13 (Go edition), One UI Core 5.1; tela 6,5\" PLS LCD "
        "720×1600 px (HD+), 60 Hz (~270 ppi); 2 GB RAM LPDDR3. Orientação retrato; "
        "sem rolagem horizontal obrigatória; elementos interativos dimensionados para toque."
    ),
    "aceite": (
        "Todas as telas RF-UI e RF-MAP-UI utilizáveis e legíveis no dispositivo de "
        "referência (ou emulador equivalente 720×1600 px); conteúdo crítico visível "
        "sem zoom."
    ),
    "prioridade": "Must",
}


def qname(ns: str, tag: str) -> str:
    return f"{{{NS[ns]}}}{tag}"


def cell_text(cell: ET.Element) -> str:
    return " ".join("".join(cell.itertext()).split())


def set_cell_text_preserve_style(cell: ET.Element, value: str) -> None:
    paras = cell.findall("text:p", NS)
    if not paras:
        para = ET.SubElement(cell, qname("text", "p"))
        span = ET.SubElement(para, qname("text", "span"))
        span.text = value
        return

    para = paras[0]
    spans = para.findall("text:span", NS)
    if spans:
        spans[0].text = value
        for extra in spans[1:]:
            para.remove(extra)
        para.text = None
    else:
        para.text = value

    for extra_para in paras[1:]:
        cell.remove(extra_para)


def fill_requirement_table(table: ET.Element, data: dict[str, str]) -> ET.Element:
    new_table = copy.deepcopy(table)
    for row in new_table.findall("table:table-row", NS):
        cells = row.findall("table:table-cell", NS)
        if len(cells) < 3:
            continue
        item = cell_text(cells[0])
        tipo = cell_text(cells[1]).lower()
        if item == "ITEM" or tipo == "tipo":
            continue
        if "descri" in tipo and item == "01":
            set_cell_text_preserve_style(cells[2], data["titulo_curto"])
        elif "requisito" in tipo:
            set_cell_text_preserve_style(cells[2], data["descricao"])
        elif "aceite" in tipo:
            set_cell_text_preserve_style(cells[2], data["aceite"])
        elif "prior" in tipo:
            set_cell_text_preserve_style(cells[2], data["prioridade"])
    return new_table


def clone_heading(template: ET.Element, req_id: str) -> ET.Element:
    p = copy.deepcopy(template)
    for child in list(p):
        p.remove(child)
    p.text = req_id
    return p


def clone_empty_paragraph(template: ET.Element) -> ET.Element:
    p = ET.Element(qname("text", "p"))
    if template.get(qname("text", "style-name")):
        p.set(qname("text", "style-name"), template.get(qname("text", "style-name")))
    return p


def find_rnf008_insert_index(text_el: ET.Element) -> int:
    children = list(text_el)
    for i, child in enumerate(children):
        if child.tag.endswith("p") and "".join(child.itertext()).strip() == "RNF-008":
            # Após: heading, empty, table, empty, empty
            return i + 5
    raise RuntimeError("Bloco RNF-008 não encontrado.")


def main() -> None:
    if not ODT_PATH.exists():
        raise FileNotFoundError(ODT_PATH)

    with zipfile.ZipFile(ODT_PATH, "r") as zin:
        content = zin.read("content.xml")

    root = ET.fromstring(content)
    text_el = root.find(".//office:text", NS)
    if text_el is None:
        raise RuntimeError("office:text não encontrado")

    if re.search(r"\bRNF-009\b", "".join(text_el.itertext())):
        print("RNF-009 já presente no ODT.")
        return

    children = list(text_el)
    insert_at = find_rnf008_insert_index(text_el)

    template_heading = children[insert_at - 5]  # RNF-008
    template_empty = children[insert_at - 4]
    template_table = children[insert_at - 3]

    new_nodes = [
        clone_empty_paragraph(template_empty),
        clone_heading(template_heading, "RNF-009"),
        clone_empty_paragraph(template_empty),
        fill_requirement_table(template_table, RNF_009),
        clone_empty_paragraph(template_empty),
    ]

    shutil.copy2(ODT_PATH, BACKUP_PATH)

    for offset, node in enumerate(new_nodes):
        text_el.insert(insert_at + offset, node)

    new_content = ET.tostring(root, encoding="utf-8", xml_declaration=True)
    temp_odt = ODT_PATH.with_suffix(".tmp.odt")
    with zipfile.ZipFile(ODT_PATH, "r") as zin, zipfile.ZipFile(temp_odt, "w") as zout:
        for item in zin.infolist():
            data = new_content if item.filename == "content.xml" else zin.read(item.filename)
            zout.writestr(item, data)

    temp_odt.replace(ODT_PATH)
    print(f"Inserido RNF-009 em {ODT_PATH}")
    print(f"Backup: {BACKUP_PATH}")


if __name__ == "__main__":
    main()

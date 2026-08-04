# -*- coding: utf-8 -*-
"""
Biblioteca compartilhada para leitura do Doc_Proj_Map.odt.

Fonte única de documentação do projeto (requisitos, regras de negócio, arquitetura).
"""

from __future__ import annotations

import re
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
ODT_PATH = BASE / "Doc" / "Doc_Proj_Map.odt"
BACKUP_PATH = BASE / "Doc" / "Doc_Proj_Map.odt.bak"

NS = {
    "office": "urn:oasis:names:tc:opendocument:xmlns:office:1.0",
    "text": "urn:oasis:names:tc:opendocument:xmlns:text:1.0",
    "table": "urn:oasis:names:tc:opendocument:xmlns:table:1.0",
}

ID_RE = re.compile(
    r"\b(RF(?:-MAP)?-(?:UI|RN)-\d+[a-z]?|RNF(?:-MAP)?-\d+[a-z]?)\b"
)


def qname(ns: str, tag: str) -> str:
    return f"{{{NS[ns]}}}{tag}"


def read_content_root() -> ET.Element:
    if not ODT_PATH.exists():
        raise FileNotFoundError(f"Documentação não encontrada: {ODT_PATH}")
    with zipfile.ZipFile(ODT_PATH, "r") as zin:
        return ET.fromstring(zin.read("content.xml"))


def get_text_element(root: ET.Element | None = None) -> ET.Element:
    root = root or read_content_root()
    text_el = root.find(".//office:text", NS)
    if text_el is None:
        raise RuntimeError("office:text não encontrado no ODT")
    return text_el


def paragraph_texts(root: ET.Element | None = None) -> list[str]:
    text_el = get_text_element(root)
    return [
        "".join(p.itertext()).strip().replace("\xa0", " ")
        for p in text_el.findall("text:p", NS)
        if "".join(p.itertext()).strip()
    ]


def documented_ids(root: ET.Element | None = None) -> set[str]:
    """IDs com parágrafo-título dedicado no ODT."""
    text_el = get_text_element(root)
    documented: set[str] = set()
    for p in text_el.findall("text:p", NS):
        raw = "".join(p.itertext()).strip().replace("\xa0", " ")
        if ID_RE.fullmatch(raw):
            documented.add(raw)
    return documented


def cell_text(cell: ET.Element) -> str:
    return " ".join("".join(cell.itertext()).split())


def requirement_tables(root: ET.Element | None = None) -> list[dict[str, str]]:
    """Extrai tabelas de requisitos (ITEM 01 = título curto)."""
    text_el = get_text_element(root)
    rows: list[dict[str, str]] = []
    current_id: str | None = None

    children = list(text_el)
    for child in children:
        if child.tag.endswith("p"):
            raw = "".join(child.itertext()).strip().replace("\xa0", " ")
            if ID_RE.fullmatch(raw):
                current_id = raw
            continue
        if not child.tag.endswith("table") or not current_id:
            continue

        data: dict[str, str] = {"id": current_id}
        for row in child.findall("table:table-row", NS):
            cells = row.findall("table:table-cell", NS)
            if len(cells) < 3:
                continue
            item = cell_text(cells[0])
            tipo = cell_text(cells[1]).lower()
            if item == "ITEM" or tipo == "tipo":
                continue
            if "descri" in tipo and item == "01":
                data["titulo_curto"] = cell_text(cells[2])
            elif "requisito" in tipo:
                data["descricao"] = cell_text(cells[2])
            elif "aceite" in tipo:
                data["aceite"] = cell_text(cells[2])
            elif "prior" in tipo:
                data["prioridade"] = cell_text(cells[2])

        if "titulo_curto" in data:
            rows.append(data)
        current_id = None

    return rows


def write_content_xml(root: ET.Element, backup: bool = True) -> None:
    shutil_copy = __import__("shutil").copy2
    if backup and ODT_PATH.exists():
        try:
            shutil_copy(ODT_PATH, BACKUP_PATH)
        except OSError:
            pass
    new_content = ET.tostring(root, encoding="utf-8", xml_declaration=True)
    temp_odt = ODT_PATH.with_suffix(".tmp.odt")
    with zipfile.ZipFile(ODT_PATH, "r") as zin, zipfile.ZipFile(temp_odt, "w") as zout:
        for item in zin.infolist():
            data = new_content if item.filename == "content.xml" else zin.read(item.filename)
            zout.writestr(item, data)
    try:
        temp_odt.replace(ODT_PATH)
    except OSError:
        # Arquivo aberto no LibreOffice/Word — grava cópia atualizada
        alt = ODT_PATH.with_name("Doc_Proj_Map.updated.odt")
        if alt.exists():
            alt.unlink()
        temp_odt.replace(alt)
        raise PermissionError(
            f"Doc_Proj_Map.odt está aberto/bloqueado. "
            f"Feche o documento e substitua por: {alt}"
        ) from None

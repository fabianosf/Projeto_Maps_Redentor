# -*- coding: utf-8 -*-
"""Insere RF-UI-019, RF-UI-020 e RF-UI-021 (telas placeholder) no Doc_Proj_Map.odt."""

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

NEW_REQUIREMENTS: list[tuple[str, dict[str, str]]] = [
    (
        "RF-UI-019",
        {
            "titulo_curto": "Telas citadas sem especificação de conteúdo",
            "descricao": (
                "Quando um requisito menciona uma tela sem detalhar campos, listas, "
                "formulários ou ações internas, o FrontEnd deverá: (1) criar a rota/tela "
                "e permitir navegação até ela; (2) exibir a tela vazia por enquanto — "
                "apenas shell (identificação mínima, fundo bege, tipografia RedMapa), "
                "sem itens de conteúdo; (3) quando houver requisitos que especifiquem "
                "a construção da mesma tela, implementar conforme esses requisitos."
            ),
            "aceite": (
                "Telas citadas sem detalhe abrem e são visíveis, porém sem conteúdo "
                "operacional; telas com RF dedicado seguem a especificação completa."
            ),
            "prioridade": "Must",
        },
    ),
    (
        "RF-UI-020",
        {
            "titulo_curto": "Tela Configuração (placeholder)",
            "descricao": (
                "Ao pressionar Configuração na tela principal (RF-UI-014), abrir a tela "
                "Configuração. Nesta versão não há requisitos de conteúdo interno — "
                "aplicar RF-UI-019: exibir tela vazia (shell). Acesso apenas para "
                "Administrador (codigo_perfil = 1; RF-UI-015)."
            ),
            "aceite": (
                "Administrador navega à tela Configuração vazia; Despachante não acessa "
                "(botão disabled)."
            ),
            "prioridade": "Must",
        },
    ),
    (
        "RF-UI-021",
        {
            "titulo_curto": "Tela Relatórios (placeholder)",
            "descricao": (
                "Ao pressionar Relatório na tela principal (RF-UI-014), abrir a tela "
                "Relatórios. Nesta versão não há requisitos de conteúdo interno — "
                "aplicar RF-UI-019: exibir tela vazia (shell). Acessível a Administrador "
                "e Despachante."
            ),
            "aceite": (
                "Usuário autenticado abre tela Relatórios vazia; sem listagens, filtros "
                "ou exportação nesta fase."
            ),
            "prioridade": "Must",
        },
    ),
]


def qname(ns: str, tag: str) -> str:
    return f"{{{NS[ns]}}}{tag}"


def cell_text(cell: ET.Element) -> str:
    return " ".join("".join(cell.itertext()).split())


def set_cell_text_preserve_style(cell: ET.Element, value: str) -> None:
    paras = cell.findall("text:p", NS)
    if not paras:
        para = ET.SubElement(cell, qname("text", "p"))
        para.text = value
        return
    para = paras[0]
    for child in list(para):
        para.remove(child)
    para.text = value
    for extra in paras[1:]:
        cell.remove(extra)


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


def find_rf_ui_018_insert_index(text_el: ET.Element) -> int:
    children = list(text_el)
    for i, child in enumerate(children):
        if child.tag.endswith("p") and "".join(child.itertext()).strip() == "RF-UI-018":
            return i + 5
    raise RuntimeError("Bloco RF-UI-018 não encontrado.")


def main() -> None:
    if not ODT_PATH.exists():
        raise FileNotFoundError(ODT_PATH)

    with zipfile.ZipFile(ODT_PATH, "r") as zin:
        content = zin.read("content.xml")

    root = ET.fromstring(content)
    text_el = root.find(".//office:text", NS)
    if text_el is None:
        raise RuntimeError("office:text não encontrado")

    existing = set(re.findall(r"\bRF-UI-\d+\b", "".join(text_el.itertext())))
    to_add = [(rid, data) for rid, data in NEW_REQUIREMENTS if rid not in existing]
    if not to_add:
        print("RF-UI-019/020/021 já presentes no ODT.")
        return

    insert_at = find_rf_ui_018_insert_index(text_el)
    children = list(text_el)
    template_heading = children[insert_at - 5]
    template_empty = children[insert_at - 4]
    template_table = children[insert_at - 3]

    new_nodes: list[ET.Element] = []
    for req_id, data in to_add:
        new_nodes.extend(
            [
                clone_empty_paragraph(template_empty),
                clone_heading(template_heading, req_id),
                clone_empty_paragraph(template_empty),
                fill_requirement_table(template_table, data),
                clone_empty_paragraph(template_empty),
            ]
        )

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
    for rid, _ in to_add:
        print(f"Inserido {rid} em {ODT_PATH}")
    print(f"Backup: {BACKUP_PATH}")


if __name__ == "__main__":
    main()

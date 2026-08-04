# -*- coding: utf-8 -*-
"""Alinha tabela RF-RN-012 no Doc_Proj_Map.odt com regras HTTP de Proj_Map_Regras_De_Negocio.md."""

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

ID_RE = re.compile(
    r"^(RF(?:-MAP)?-(?:UI|RN)-\d+[a-z]?|RNF(?:-MAP)?-\d+[a-z]?)$"
)

RF_RN_012 = {
    "titulo_curto": "Contrato API de autenticação (regras HTTP)",
    "descricao": (
        "BackEnd Flask expõe JSON em /api/v1/auth/* e /api/v1/health. "
        "Endpoints: POST /login, POST /change-password, POST /cancel-change-password, "
        "POST /cancel-login, POST /logout, GET /me, GET /health. "
        "Regras HTTP: Login inválido → 401 (login inválido!, codigo: login_invalido); "
        "Sessão inválida → 401 (Operação não autorizada., codigo: sessao_invalida); "
        "Validação senha nova → 400 (mensagem RF-RN-006); "
        "Login OK sem troca → 200 (JSON usuário + Set-Cookie: redmapa_sid); "
        "Login OK com troca → 200 (JSON + change_token, sem cookie de sessão); "
        "Troca senha OK → 200 (sucesso, sem cookie de sessão)."
    ),
    "aceite": (
        "Contratos HTTP conforme Proj_Map_Regras_De_Negocio.md (RF-RN-012) e "
        "Requisitos_Ciclo_Login_MAP.md §9.4."
    ),
    "prioridade": "Must",
}


def qname(ns: str, tag: str) -> str:
    return f"{{{NS[ns]}}}{tag}"


def cell_text(cell: ET.Element) -> str:
    return " ".join("".join(cell.itertext()).split())


def set_cell_text(cell: ET.Element, value: str) -> None:
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


def fill_table(table: ET.Element, data: dict[str, str]) -> None:
    for row in table.findall("table:table-row", NS):
        cells = row.findall("table:table-cell", NS)
        if len(cells) < 3:
            continue
        item = cell_text(cells[0])
        tipo = cell_text(cells[1]).lower()
        if item == "ITEM" or tipo == "tipo":
            continue
        if "descri" in tipo and item == "01":
            set_cell_text(cells[2], data["titulo_curto"])
        elif "requisito" in tipo:
            set_cell_text(cells[2], data["descricao"])
        elif "aceite" in tipo:
            set_cell_text(cells[2], data["aceite"])
        elif "prior" in tipo:
            set_cell_text(cells[2], data["prioridade"])


def find_rf_rn_012_table(text_el: ET.Element) -> ET.Element | None:
    """Localiza a tabela funcional RF-RN-012 (primeira ocorrência com endpoints Flask)."""
    children = list(text_el)
    for i, child in enumerate(children):
        if not child.tag.endswith("p"):
            continue
        raw = "".join(child.itertext()).strip().replace("\xa0", " ")
        if raw != "RF-RN-012":
            continue
        if i + 2 < len(children) and children[i + 2].tag.endswith("table"):
            table = children[i + 2]
            flat = "".join(table.itertext())
            if "/api/v1/auth" in flat or "API REST" in flat or "Flask" in flat:
                return table
    # fallback: primeira tabela após heading RF-RN-012
    for i, child in enumerate(children):
        if child.tag.endswith("p") and "".join(child.itertext()).strip().replace("\xa0", " ") == "RF-RN-012":
            if i + 2 < len(children) and children[i + 2].tag.endswith("table"):
                return children[i + 2]
    return None


def main() -> None:
    if not ODT_PATH.exists():
        raise FileNotFoundError(ODT_PATH)

    shutil.copy2(ODT_PATH, BACKUP_PATH)

    with zipfile.ZipFile(ODT_PATH, "r") as zin:
        content = zin.read("content.xml")

    root = ET.fromstring(content)
    text_el = root.find(".//office:text", NS)
    if text_el is None:
        raise RuntimeError("office:text não encontrado")

    table = find_rf_rn_012_table(text_el)
    if table is None:
        raise RuntimeError("Tabela RF-RN-012 não encontrada no ODT.")

    fill_table(table, RF_RN_012)
    print("RF-RN-012 atualizado com regras HTTP.")

    new_content = ET.tostring(root, encoding="utf-8", xml_declaration=True)
    temp_odt = ODT_PATH.with_suffix(".tmp.odt")
    with zipfile.ZipFile(ODT_PATH, "r") as zin, zipfile.ZipFile(temp_odt, "w") as zout:
        for item in zin.infolist():
            data = new_content if item.filename == "content.xml" else zin.read(item.filename)
            zout.writestr(item, data)
    temp_odt.replace(ODT_PATH)
    print(f"Atualizado: {ODT_PATH}")


if __name__ == "__main__":
    main()

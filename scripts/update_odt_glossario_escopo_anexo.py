# -*- coding: utf-8 -*-
"""
Atualiza Doc_Proj_Map.odt:
  - Seção 2.6: substitui tabela de funcionalidades pelo escopo RedMapa
  - Seção 9: glossário técnico (tabela ITEM | TERMO | DESCRIÇÃO)
  - Seção 10: anexo com características do Samsung Galaxy A03 Core
"""

from __future__ import annotations

import copy
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

# --- 2.6.1 Funcionalidades RedMapa (mantém colunas Cod | Recursos | Descrição) ---
ESCOPO_FUNCIONALIDADES: list[tuple[str, str, str]] = [
    (
        "01",
        "Autenticação de usuário",
        "Login por matrícula e senha; troca obrigatória de senha provisória no primeiro acesso; "
        "logout (Sair) com invalidação de sessão.",
    ),
    (
        "02",
        "Controle de acesso",
        "Perfis Administrador (codigo_perfil = 1) e Despachante (codigo_perfil = 2); "
        "autorização conforme perfil armazenado na sessão server-side.",
    ),
    (
        "03",
        "Lista de MAPAS (Lista_mapa)",
        "Listagem tabular de MAPAS (número, empresa, linha, turno); seleção para edição; "
        'inclusão de novo MAPA via ícone "+".',
    ),
    (
        "04",
        "Cadastro de MAPA (Cad_mapa)",
        "Formulário de cabeçalho (data, início/fim de jornada, empresa, linha, turno); "
        "cod_map gerado automaticamente; modos inclusão e edição.",
    ),
    (
        "05",
        "Tela Mapa (detalhe operacional)",
        "Gestão de carros (tb_item_map) e viagens (tb_viagem) do MAPA selecionado; "
        "edição de cabeçalho, carros e viagens conforme regras de negócio.",
    ),
    (
        "06",
        "Interface mobile-first",
        "FrontEnd WEB responsivo (HTML, CSS, JavaScript) otimizado para smartphone; "
        "identidade visual RedMapa (shell bege, fonte Calibri).",
    ),
    (
        "07",
        "API REST (BackEnd Python/Flask)",
        "Endpoints de autenticação (/api/v1/auth/*) implementados; endpoints do módulo MAPA "
        "conforme requisitos; respostas em JSON.",
    ),
    (
        "08",
        "Persistência e integridade de dados",
        "Armazenamento em MariaDB (banco map); acesso via DAL (pool de conexões, cache, "
        "circuit breaker); configurações criptografadas (Fernet).",
    ),
]

# --- Glossário RedMapa: ITEM | TERMO | DESCRIÇÃO ---
GLOSSARIO: list[tuple[str, str, str]] = [
    ("01", "MAPA", "Documento operacional que registra, por data/turno/linha, os carros alocados e suas viagens."),
    ("02", "RedMapa", "Nome da aplicação WEB de gestão de MAPAS operacionais do Grupo Redentor."),
    ("03", "PROJ_MAP", "Identificador do repositório e do projeto de desenvolvimento do RedMapa."),
    ("04", "API REST", "Interface HTTP que expõe recursos do sistema em JSON; prefixo base /api/v1."),
    ("05", "Flask", "Framework Python usado no BackEnd para rotas HTTP, JSON e cookies de sessão."),
    ("06", "MariaDB", "SGBD relacional principal do projeto; banco de dados map."),
    ("07", "DAL", "Data Access Layer — camada Python (DAL.py) responsável por conexões, queries e resiliência ao banco."),
    ("08", "bcrypt", "Algoritmo de hash para senhas (cost 12); senhas nunca armazenadas em texto puro."),
    ("09", "Fernet", "Criptografia simétrica usada nos arquivos .dat de configuração (DAL/arquivos_crip/chave/chave.key)."),
    ("10", "redmapa_sid", "Cookie HttpOnly que identifica a sessão autenticada no servidor."),
    ("11", "HttpOnly", "Atributo de cookie que impede acesso via JavaScript, mitigando roubo por XSS."),
    ("12", "FrontEnd", "Camada de apresentação: telas HTML/CSS/JS executadas no navegador do dispositivo."),
    ("13", "BackEnd", "Camada servidor: API Python, regras de negócio, sessão e acesso a dados."),
    ("14", "Mobile-first", "Abordagem de design que prioriza uso em smartphone (viewport ≥ 360 px)."),
    ("15", "Despachante", "Perfil operacional (codigo_perfil = 2) que elabora e mantém MAPAS no dia a dia."),
    ("16", "Administrador", "Perfil de gestão (codigo_perfil = 1) com acesso ao módulo MAPA."),
    ("17", "tb_map", "Tabela do cabeçalho do MAPA (data, jornada, empresa, linha, turno, despachante)."),
    ("18", "tb_item_map", "Tabela dos carros/itens vinculados a um MAPA."),
    ("19", "tb_viagem", "Tabela das viagens associadas a cada carro (item) do MAPA."),
    ("20", "pymysql", "Driver Python para conexão da API ao MariaDB/MySQL."),
    ("21", "JSON", "Formato de troca de dados entre browser e API (Content-Type: application/json)."),
    ("22", "Sessão server-side", "Estado autenticado mantido em memória no Flask; cookie opaco no cliente."),
    ("23", "change_token", "Token temporário (15 min) emitido no primeiro acesso para troca de senha sem sessão plena."),
    ("24", "PROJ_GAC", "Utilitário legado de geração de arquivos de configuração criptografados (.dat)."),
    ("25", "RF-UI / RF-MAP-UI", "Prefixos de requisitos funcionais de interface (login e módulo MAPA)."),
    ("26", "Must / Should / Could", "Prioridades de requisito: obrigatório, desejável ou opcional."),
    ("27", "Modal Rodoviário", "Meio de transporte por ônibus/caminhão em vias urbanas ou rodoviárias."),
    ("28", "Consórcio", "Agrupamento de empresas de transporte que operam uma área geográfica licitada."),
]

# --- Anexo: Samsung Galaxy A03 Core ---
SMARTPHONE_SPECS: list[tuple[str, str, str]] = [
    ("01", "Modelo", "Samsung Galaxy A03 Core (SM-A032F)"),
    ("02", "Sistema operacional", "Android 13 (Go edition), One UI Core 5.1"),
    ("03", "Processador (SoC)", "Unisoc SC9863A — Octa-core (4×1,6 GHz + 4×1,2 GHz Cortex-A55)"),
    ("04", "GPU", "PowerVR GE8322"),
    ("05", "Memória RAM", "2 GB LPDDR3"),
    ("06", "Armazenamento interno", "32 GB eMMC 5.1"),
    ("07", "Expansão de memória", "microSDXC dedicado (até 1 TB)"),
    ("08", "Tela", '6,5" PLS LCD, 720×1600 px (HD+), 60 Hz, ~270 ppi'),
    ("09", "Câmera traseira", "8 MP, f/2.0, autofoco, LED flash, vídeo 1080p@30fps"),
    ("10", "Câmera frontal", "5 MP, f/2.2"),
    ("11", "Bateria", "5000 mAh Li-Ion (não removível)"),
    ("12", "Conectividade móvel", "GSM / HSPA / LTE (4G)"),
    ("13", "Wi-Fi", "802.11 b/g/n 2,4 GHz, Wi-Fi Direct"),
    ("14", "Bluetooth", "4.2, A2DP"),
    ("15", "GPS", "GPS, GLONASS"),
    ("16", "USB", "microUSB 2.0, OTG"),
    ("17", "SIM", "Nano-SIM (single ou dual SIM + microSD)"),
    ("18", "Dimensões", "164,2 × 75,9 × 9,1 mm"),
    ("19", "Peso", "211 g"),
    ("20", "Áudio", "Alto-falante e conector P2 (3,5 mm)"),
]


def qname(ns: str, tag: str) -> str:
    return f"{{{NS[ns]}}}{tag}"


def para_text(el: ET.Element) -> str:
    return " ".join("".join(el.itertext()).split())


def set_cell_text(cell: ET.Element, value: str) -> None:
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


def make_paragraph(style: str, text: str | None = None) -> ET.Element:
    p = ET.Element(qname("text", "p"))
    p.set(qname("text", "style-name"), style)
    if text:
        p.text = text
    return p


def clone_heading(template: ET.Element, title: str) -> ET.Element:
    p = copy.deepcopy(template)
    for child in list(p):
        p.remove(child)
    p.text = title
    return p


def build_3col_table(
    template: ET.Element,
    header: tuple[str, str, str],
    rows: list[tuple[str, str, str]],
) -> ET.Element:
    tbl = copy.deepcopy(template)
    data_rows = tbl.findall("table:table-row", NS)
    proto_header, proto_data = data_rows[0], data_rows[1]
    for row in data_rows:
        tbl.remove(row)
    hdr = copy.deepcopy(proto_header)
    cells = hdr.findall("table:table-cell", NS)
    for i, val in enumerate(header):
        set_cell_text(cells[i], val)
    tbl.append(hdr)
    for triple in rows:
        row = copy.deepcopy(proto_data)
        cells = row.findall("table:table-cell", NS)
        for i, val in enumerate(triple):
            set_cell_text(cells[i], val)
        tbl.append(row)
    return tbl


def find_paragraph_index(text_el: ET.Element, predicate) -> int:
    for i, child in enumerate(list(text_el)):
        if child.tag == qname("text", "p") and predicate(para_text(child)):
            return i
    raise RuntimeError("Parágrafo não encontrado")


def find_next_table_index(text_el: ET.Element, after_idx: int) -> int:
    children = list(text_el)
    for i in range(after_idx + 1, len(children)):
        if children[i].tag == qname("table", "table"):
            return i
    raise RuntimeError("Tabela não encontrada após índice informado")


def replace_escopo_table(text_el: ET.Element) -> None:
    idx = find_paragraph_index(
        text_el, lambda t: t.strip().startswith("2.6.1") and "oferece" in t.lower()
    )
    table_idx = find_next_table_index(text_el, idx)
    children = list(text_el)
    template = children[table_idx]
    new_table = build_3col_table(
        template,
        ("Cod", "Recursos", "Descrição"),
        ESCOPO_FUNCIONALIDADES,
    )
    text_el.remove(template)
    text_el.insert(table_idx, new_table)
    print(f"Escopo 2.6.1: tabela atualizada ({len(ESCOPO_FUNCIONALIDADES)} funcionalidades)")


def replace_glossary(text_el: ET.Element) -> None:
    idx = find_paragraph_index(text_el, lambda t: t.strip().startswith("9.") and "Gloss" in t)
    table_idx = find_next_table_index(text_el, idx)
    children = list(text_el)
    template = children[table_idx]
    new_table = build_3col_table(
        template,
        ("ITEM", "TERMO", "DESCRIÇÃO"),
        GLOSSARIO,
    )
    text_el.remove(template)
    text_el.insert(table_idx, new_table)
    print(f"Glossário: {len(GLOSSARIO)} termos")


def append_smartphone_anexo(text_el: ET.Element) -> None:
    children = list(text_el)

    # Templates de estilo
    gloss_heading = None
    gloss_table_tpl = None
    for i, child in enumerate(children):
        if child.tag == qname("text", "p") and para_text(child).startswith("9.") and "Gloss" in para_text(child):
            gloss_heading = child
            gloss_table_tpl = children[find_next_table_index(text_el, i)]
            break
    if gloss_heading is None or gloss_table_tpl is None:
        raise RuntimeError("Template de glossário não encontrado")

    # Estilo de subseção (ex.: 8.1)
    sub_heading = None
    for child in children:
        if child.tag == qname("text", "p") and para_text(child).startswith("8.1"):
            sub_heading = child
            break
    if sub_heading is None:
        sub_heading = gloss_heading

    note_style = "P862"
    body_style = "P860"
    gap_style = "P85"

    nodes: list[ET.Element] = [
        make_paragraph(gap_style),
        make_paragraph(gap_style),
        clone_heading(gloss_heading, "10. Anexo"),
        make_paragraph(gap_style),
        clone_heading(sub_heading, "10.) Dispositivo (Smartphone) utilizado no projeto"),
        make_paragraph(gap_style),
        make_paragraph(
            note_style,
            'Nota: O smartphone de referência para desenvolvimento e testes mobile-first é o '
            '"Samsung Galaxy A03 Core" (Android 13 — Go edition).',
        ),
        make_paragraph(gap_style),
        clone_heading(sub_heading, "10.1 Características técnicas"),
        make_paragraph(gap_style),
        build_3col_table(
            gloss_table_tpl,
            ("ITEM", "CARACTERÍSTICA", "ESPECIFICAÇÃO"),
            SMARTPHONE_SPECS,
        ),
        make_paragraph(gap_style),
    ]

    for node in nodes:
        text_el.append(node)

    print(f"Anexo 10: Samsung Galaxy A03 Core ({len(SMARTPHONE_SPECS)} características)")


def main() -> None:
    if not ODT_PATH.exists():
        raise FileNotFoundError(ODT_PATH)

    shutil.copy2(ODT_PATH, BACKUP_PATH)

    with zipfile.ZipFile(ODT_PATH, "r") as zin:
        content = zin.read("content.xml")
        archive = {info.filename: zin.read(info.filename) for info in zin.infolist()}

    root = ET.fromstring(content)
    text_el = root.find(".//office:text", NS)
    if text_el is None:
        raise RuntimeError("office:text não encontrado")

    replace_escopo_table(text_el)
    replace_glossary(text_el)
    append_smartphone_anexo(text_el)

    archive["content.xml"] = ET.tostring(root, encoding="utf-8", xml_declaration=True)

    temp_odt = ODT_PATH.with_suffix(".tmp.odt")
    with zipfile.ZipFile(temp_odt, "w", compression=zipfile.ZIP_DEFLATED) as zout:
        for name, data in archive.items():
            zout.writestr(name, data)

    temp_odt.replace(ODT_PATH)
    print(f"Atualizado: {ODT_PATH}")
    print(f"Backup: {BACKUP_PATH}")


if __name__ == "__main__":
    main()

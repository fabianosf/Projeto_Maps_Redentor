# -*- coding: utf-8 -*-
"""
Substitui regras de negócio de autenticação/cadastro na seção 6.3 do Doc_Proj_Map.odt.

Mantém intactas: RF-RN-008, RF-RN-008a, RF-RN-010, RF-RN-011 (sessão) e RF-MAP-RN-*.
RF-RN-012 (contrato API) permanece na seção de integração.
"""

from __future__ import annotations

import copy
import re
import shutil
import zipfile
from pathlib import Path
import xml.etree.ElementTree as ET

from odt_lib import BACKUP_PATH, ODT_PATH, NS, read_content_root, write_content_xml

ID_RE = re.compile(r"^RF-RN-\d+[a-z]?$")

# Regras novas (substituem RF-RN-001 … RF-RN-007 e RF-RN-009)
AUTH_RULES: list[tuple[str, dict[str, str], str | None]] = [
    (
        "RF-RN-001",
        {
            "titulo_curto": "Perfis do sistema",
            "descricao": (
                "O sistema possui dois perfis cadastrados em tb_perfil: "
                "Administrador (codigo_perfil = 1) e Despachante (codigo_perfil = 2). "
                "Todo usuário em tb_usuario referencia id_perfil (FK tb_perfil)."
            ),
            "aceite": "Seeds e cadastros utilizam somente perfis 1 e 2.",
            "prioridade": "Must",
        },
        None,
    ),
    (
        "RF-RN-002",
        {
            "titulo_curto": "Acesso por login (matrícula e senha)",
            "descricao": (
                "O acesso à aplicação exige autenticação na tela Login: matrícula "
                "(campo Usuário) e senha obrigatórios. BackEnd valida via API "
                "/api/v1/auth/login contra tb_usuario."
            ),
            "aceite": "Campos vazios ou credenciais inválidas impedem acesso autenticado.",
            "prioridade": "Must",
        },
        "Regras de negócio — Login e autenticação:",
    ),
    (
        "RF-RN-003",
        {
            "titulo_curto": "Identificação por matrícula",
            "descricao": (
                "O usuário é identificado exclusivamente pela matrícula "
                "(tb_usuario.matricula, UNIQUE). A UI aceita somente dígitos "
                "no campo Usuário (RF-UI-006)."
            ),
            "aceite": "Login localiza registro por matricula antes de validar senha.",
            "prioridade": "Must",
        },
        None,
    ),
    (
        "RF-RN-004",
        {
            "titulo_curto": "Primeiro acesso (senha padrão 12345)",
            "descricao": (
                "Primeiro acesso identificado por trocar_senha = 1. Senha provisória "
                "conhecida = 12345 (texto claro). No cadastro pelo Administrador ou após "
                "reset, tb_usuario.senha armazena hash bcrypt de 12345; trocar_senha = 1."
            ),
            "aceite": "Login com 12345 autentica quando trocar_senha = 1.",
            "prioridade": "Must",
        },
        None,
    ),
    (
        "RF-RN-005",
        {
            "titulo_curto": "Cadastro da senha definitiva (1º acesso)",
            "descricao": (
                "Após login OK com trocar_senha = 1, exibir Cadastro de senha. "
                "Usuário informa nova senha e confirmação (2 campos iguais). "
                "BackEnd valida política (RF-RN-007), gera hash bcrypt (cost 12), "
                "UPDATE tb_usuario SET senha = hash, trocar_senha = 0; invalida "
                "change_token; retorna ao Login sem sessão."
            ),
            "aceite": "Confirmação divergente ou política inválida bloqueiam gravação.",
            "prioridade": "Must",
        },
        "Regras de negócio — Senha e criptografia:",
    ),
    (
        "RF-RN-006",
        {
            "titulo_curto": "Armazenamento de senha em hash bcrypt",
            "descricao": (
                "tb_usuario.senha armazena exclusivamente hash bcrypt (cost 12, "
                "formato $2b$12$...). Proibido texto puro ou criptografia reversível. "
                "Login valida com bcrypt.verify; FrontEnd nunca acessa a coluna senha."
            ),
            "aceite": "Todos os registros possuem hash bcrypt válido.",
            "prioridade": "Must",
        },
        None,
    ),
    (
        "RF-RN-007",
        {
            "titulo_curto": "Política da senha definitiva",
            "descricao": (
                "Senha definitiva: alfanumérica, mínimo 8 caracteres, ao menos 1 "
                "caractere especial. Validação idêntica no FrontEnd (pré-check) e "
                "BackEnd (obrigatório). Senha provisória 12345 não precisa cumprir "
                "esta política."
            ),
            "aceite": "Senha fora da política retorna mensagem de validação (RF-UI-011).",
            "prioridade": "Must",
        },
        None,
    ),
    (
        "RF-RN-009",
        {
            "titulo_curto": "Resultado da autenticação no login",
            "descricao": (
                "Ordem: (1) localizar por matricula; (2) se ativo = 0 → negar com "
                "mensagem genérica; (3) validar hash bcrypt; (4) se incorreta → negar; "
                "(5) se OK e trocar_senha = 1 → Cadastro de senha; (6) se OK e "
                "trocar_senha = 0 → tela principal autenticada (RF-UI-013)."
            ),
            "aceite": "Credenciais corretas + ativo = 1 concedem fluxo pós-login adequado.",
            "prioridade": "Must",
        },
        None,
    ),
]

USER_ADMIN_RULES: list[tuple[str, dict[str, str], str | None]] = [
    (
        "RF-RN-013",
        {
            "titulo_curto": "Cadastro de usuários (somente Administrador)",
            "descricao": (
                "Módulo de cadastro de usuários acessível apenas por perfil "
                "Administrador (codigo_perfil = 1) via tela Configuração (RF-UI-020). "
                "Despachante não acessa cadastro (RF-UI-015). BackEnd exige sessão "
                "Admin em /api/v1/users/*."
            ),
            "aceite": "Despachante recebe 403 ou UI desabilitada no cadastro.",
            "prioridade": "Must",
        },
        "Regras de negócio — Cadastro de usuários:",
    ),
    (
        "RF-RN-014",
        {
            "titulo_curto": "Funcionalidades do cadastro de usuários",
            "descricao": (
                "O módulo Admin deve permitir: (1) cadastrar novo usuário com matrícula, "
                "nome e perfil (INSERT tb_usuario; senha inicial hash de 12345; "
                "trocar_senha = 1); (2) excluir usuário (DELETE); (3) editar perfil "
                "(UPDATE id_perfil); (4) resetar senha (botão dedicado — RF-RN-015)."
            ),
            "aceite": "CRUD reflete tb_usuario e tb_perfil conforme operações listadas.",
            "prioridade": "Must",
        },
        None,
    ),
    (
        "RF-RN-015",
        {
            "titulo_curto": "Reset de senha pelo Administrador",
            "descricao": (
                "Ação Reset senha no cadastro de usuários: UPDATE tb_usuario SET "
                "senha = hash bcrypt de 12345, trocar_senha = 1. Usuário deve "
                "realizar novo primeiro acesso com 12345 e cadastrar senha definitiva."
            ),
            "aceite": "Após reset, login com senha pessoal anterior falha; 12345 exige troca.",
            "prioridade": "Must",
        },
        None,
    ),
]

SESSION_KEEP = {"RF-RN-008", "RF-RN-008a", "RF-RN-010", "RF-RN-011"}


def qname(ns: str, tag: str) -> str:
    return f"{{{NS[ns]}}}{tag}"


def cell_text(cell: ET.Element) -> str:
    return " ".join("".join(cell.itertext()).split())


def para_text(p: ET.Element) -> str:
    return "".join(p.itertext()).strip().replace("\xa0", " ")


def find_rn_table_template(children: list[ET.Element]) -> tuple[ET.Element, ET.Element, ET.Element]:
    for i, child in enumerate(children):
        if not child.tag.endswith("p"):
            continue
        if para_text(child) == "RF-RN-008":
            return children[i], children[i + 1], children[i + 2]
    raise RuntimeError("Bloco RF-RN-008 (modelo) não encontrado.")


def find_section_para(children: list[ET.Element], substring: str) -> ET.Element:
    for child in children:
        if child.tag.endswith("p") and substring in para_text(child):
            return child
    raise RuntimeError(f"Subseção '{substring}' não encontrada.")


def clone_empty_paragraph(template_p: ET.Element) -> ET.Element:
    p = ET.Element(qname("text", "p"))
    style = template_p.get(qname("text", "style-name"))
    if style:
        p.set(qname("text", "style-name"), style)
    return p


def clone_heading(template_heading: ET.Element, req_id: str) -> ET.Element:
    p = copy.deepcopy(template_heading)
    for child in list(p):
        p.remove(child)
    p.text = req_id
    return p


def clone_section_heading(template_section: ET.Element, title: str) -> ET.Element:
    p = copy.deepcopy(template_section)
    for child in list(p):
        p.remove(child)
    p.text = title
    return p


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


def fill_table(table: ET.Element, data: dict[str, str]) -> ET.Element:
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
            set_cell_text(cells[2], data["titulo_curto"])
        elif "requisito" in tipo:
            set_cell_text(cells[2], data["descricao"])
        elif "aceite" in tipo:
            set_cell_text(cells[2], data["aceite"])
        elif "prior" in tipo:
            set_cell_text(cells[2], data["prioridade"])
    return new_table


def build_block(
    heading_tpl: ET.Element,
    empty_tpl: ET.Element,
    table_tpl: ET.Element,
    req_id: str,
    data: dict[str, str],
) -> list[ET.Element]:
    return [
        clone_empty_paragraph(empty_tpl),
        clone_heading(heading_tpl, req_id),
        clone_empty_paragraph(empty_tpl),
        fill_table(table_tpl, data),
        clone_empty_paragraph(empty_tpl),
    ]


def build_rules_block(
    rules: list[tuple[str, dict[str, str], str | None]],
    heading_tpl: ET.Element,
    empty_tpl: ET.Element,
    table_tpl: ET.Element,
    section_tpl: ET.Element,
) -> list[ET.Element]:
    nodes: list[ET.Element] = []
    for req_id, data, section_title in rules:
        if section_title:
            nodes.append(clone_empty_paragraph(empty_tpl))
            nodes.append(clone_section_heading(section_tpl, section_title))
            nodes.append(clone_empty_paragraph(empty_tpl))
        nodes.extend(build_block(heading_tpl, empty_tpl, table_tpl, req_id, data))
    return nodes


def find_section_index(children: list[ET.Element], title: str, *, exact: bool = False) -> int:
    for i, child in enumerate(children):
        if not child.tag.endswith("p"):
            continue
        text = para_text(child)
        if exact:
            if text == title:
                return i
        elif title in text:
            return i
    raise RuntimeError(f"Seção '{title}' não encontrada.")


def find_heading_block_end(children: list[ET.Element], start: int) -> int:
    """Retorna índice após bloco RF-RN (empty + id + empty + table + empty)."""
    i = start + 1
    while i < len(children) and not children[i].tag.endswith("table"):
        i += 1
    while i < len(children) and not (
        children[i].tag.endswith("p") and not para_text(children[i])
    ):
        i += 1
    return i + 1 if i < len(children) else i


def remove_range(text_el: ET.Element, start: int, end: int) -> None:
    children = list(text_el)
    for idx in range(end - 1, start - 1, -1):
        text_el.remove(children[idx])


def insert_nodes(text_el: ET.Element, index: int, nodes: list[ET.Element]) -> None:
    for offset, node in enumerate(nodes):
        text_el.insert(index + offset, node)


def update_rn012_api_table(text_el: ET.Element) -> bool:
    """Atualiza mensagem de validação de senha no RF-RN-012 (integração API)."""
    for child in text_el.findall(".//table:table", NS):
        flat = " ".join(
            cell_text(c)
            for r in child.findall("table:table-row", NS)
            for c in r.findall("table:table-cell", NS)
        )
        if "Contrato API de autenticação" in flat or "Contrato API de autentica" in flat:
            for row in child.findall("table:table-row", NS):
                cells = row.findall("table:table-cell", NS)
                if len(cells) < 3:
                    continue
                body = cell_text(cells[2])
                if "Validação senha nova" in body or "RF-RN-006" in body or "RF-RN-007" in body:
                    set_cell_text(
                        cells[2],
                        "Mensagem específica RF-RN-007 (política alfanumérica, 8+, especial)",
                    )
                    return True
    return False


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

    children = list(text_el)
    heading_tpl, empty_tpl, table_tpl = find_rn_table_template(children)
    login_section_tpl = find_section_para(children, "Login e autentica")
    user_section_tpl = clone_section_heading(
        login_section_tpl, "Regras de negócio — Cadastro de usuários:"
    )

    idx_63 = find_section_index(children, "6.3 Regras de negócio", exact=True)
    idx_session = find_section_index(children, "Regras de negócio — Sessão e autorização:", exact=True)

    # Remover blocos antigos entre 6.3 e sessão (RF-RN-001 … RF-RN-009)
    remove_range(text_el, idx_63 + 1, idx_session)

    children = list(text_el)
    idx_session = find_section_index(children, "Regras de negócio — Sessão e autorização:", exact=True)

    auth_nodes = build_rules_block(
        AUTH_RULES, heading_tpl, empty_tpl, table_tpl, login_section_tpl
    )
    insert_nodes(text_el, idx_session, auth_nodes)

    # Inserir cadastro de usuários após RF-RN-011
    children = list(text_el)
    idx_mapa = find_section_index(children, "Regras de negócio — Módulo MAPA:", exact=True)
    admin_nodes = build_rules_block(
        USER_ADMIN_RULES, heading_tpl, empty_tpl, table_tpl, user_section_tpl
    )
    insert_nodes(text_el, idx_mapa, admin_nodes)

    updated_api = update_rn012_api_table(text_el)

    new_content = ET.tostring(root, encoding="utf-8", xml_declaration=True)
    temp_odt = ODT_PATH.with_suffix(".tmp.odt")
    with zipfile.ZipFile(ODT_PATH, "r") as zin, zipfile.ZipFile(temp_odt, "w") as zout:
        for item in zin.infolist():
            data = new_content if item.filename == "content.xml" else zin.read(item.filename)
            zout.writestr(item, data)
    temp_odt.replace(ODT_PATH)

    print(f"Atualizado: {ODT_PATH}")
    print(f"Backup: {BACKUP_PATH}")
    print(f"Regras auth inseridas: {len(AUTH_RULES)}")
    print(f"Regras cadastro Admin: {len(USER_ADMIN_RULES)}")
    print(f"RF-RN-012 API atualizado: {updated_api}")


if __name__ == "__main__":
    main()

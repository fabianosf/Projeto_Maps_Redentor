# -*- coding: utf-8 -*-
"""
Atualiza Doc_Proj_Map.odt a partir de regras definidas em scripts (fonte de verdade: ODT).
Usa odt_lib para leitura/escrita do ODT.
"""

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
    r"\b(RF(?:-MAP)?-(?:UI|RN)-\d+[a-z]?|RNF(?:-MAP)?-\d+[a-z]?)\b"
)

RF_UI_013 = {
    "titulo_curto": "Destino pós-login (módulo MAPA)",
    "descricao": (
        "Após login válido sem troca obrigatória, exibir Lista_mapa — perfis "
        "Administrador e Despachante. A tela Mapa (detalhe de um MAPA) é distinta "
        "e aberta somente após seleção na lista."
    ),
    "aceite": (
        "Usuário autenticado chega à Lista_mapa; detalhe Mapa exige seleção "
        "prévia na lista."
    ),
    "prioridade": "Must",
}

# Proj_Map — ordem documentada no Doc_Proj_Map.odt (v1.1)
BUSINESS_RULES: list[tuple[str, dict[str, str], str | None]] = [
    (
        "RF-RN-001",
        {
            "titulo_curto": "Perfis do sistema",
            "descricao": (
                "O sistema possui dois perfis em tb_perfil: Administrador (codigo_perfil = 1) "
                "e Despachante (codigo_perfil = 2). Todo usuário referencia id_perfil."
            ),
            "aceite": "Seeds e cadastros utilizam somente perfis 1 e 2.",
            "prioridade": "Must",
        },
        "6.3 Regras de negócio",
    ),
    (
        "RF-RN-002",
        {
            "titulo_curto": "Acesso por login (matrícula e senha)",
            "descricao": (
                "Acesso exige matrícula e senha na tela Login. BackEnd valida via "
                "/api/v1/auth/login contra tb_usuario."
            ),
            "aceite": "Credenciais inválidas impedem acesso autenticado.",
            "prioridade": "Must",
        },
        "Regras de negócio — Login e autenticação:",
    ),
    (
        "RF-RN-003",
        {
            "titulo_curto": "Identificação por matrícula",
            "descricao": (
                "Usuário identificado por tb_usuario.matricula (UNIQUE). UI aceita somente "
                "dígitos no campo Usuário (RF-UI-006)."
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
                "Primeiro acesso: trocar_senha = 1; senha provisória 12345; banco armazena "
                "hash bcrypt de 12345 no cadastro Admin ou reset."
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
                "Cadastro de senha: confirmar 2x; validar RF-RN-007; hash bcrypt cost 12; "
                "UPDATE senha + trocar_senha = 0; invalidar change_token; voltar ao Login."
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
                "tb_usuario.senha = hash bcrypt cost 12; proibido texto puro; login usa "
                "bcrypt.verify; FrontEnd nunca acessa senha."
            ),
            "aceite": "Formato $2b$12$... em todos os registros.",
            "prioridade": "Must",
        },
        None,
    ),
    (
        "RF-RN-007",
        {
            "titulo_curto": "Política da senha definitiva",
            "descricao": (
                "Senha definitiva: alfanumérica, mínimo 8 caracteres, 1 caractere especial. "
                "Validação idêntica FrontEnd e BackEnd."
            ),
            "aceite": "Senha fora da política retorna mensagem RF-UI-011.",
            "prioridade": "Must",
        },
        None,
    ),
    (
        "RF-RN-009",
        {
            "titulo_curto": "Resultado da autenticação no login",
            "descricao": (
                "Ordem: matricula → ativo=1 → bcrypt.verify → trocar_senha=1 Cad. senha; "
                "trocar_senha=0 tela principal. Inativo ou senha errada → negar."
            ),
            "aceite": "Credenciais corretas + ativo = 1 concedem fluxo pós-login.",
            "prioridade": "Must",
        },
        None,
    ),
    (
        "RF-RN-008",
        {
            "titulo_curto": "Sessão autenticada",
            "descricao": (
                "Sessão server-side em memória; cookie redmapa_sid (HttpOnly, SameSite=Lax, "
                "Secure prod.); TTL 8 h renovação deslizante; payload id_usuario, matricula, "
                "codigo_perfil, nome; criar se trocar_senha = 0; uma sessão por usuário."
            ),
            "aceite": "Recarregar com cookie válido mantém autenticação.",
            "prioridade": "Must",
        },
        "Regras de negócio — Sessão e autorização:",
    ),
    (
        "RF-RN-008a",
        {
            "titulo_curto": "Token de troca de senha",
            "descricao": (
                "Login OK com trocar_senha = 1: change_token opaco no JSON (sem cookie); "
                "TTL 15 min; escopo apenas troca de senha; single-use; FrontEnd guarda "
                "somente em memória JS."
            ),
            "aceite": "Token expirado exige novo login.",
            "prioridade": "Must",
        },
        None,
    ),
    (
        "RF-RN-010",
        {
            "titulo_curto": "Validação de sessão em rotas protegidas",
            "descricao": (
                "Ler cookie redmapa_sid; resolver sessão; inválida → 401 JSON genérico; "
                "válida → renovar TTL e expor id_usuario, matricula, codigo_perfil; "
                "revalidar ativo = 1 no banco."
            ),
            "aceite": "APIs protegidas exigem sessão válida.",
            "prioridade": "Must",
        },
        None,
    ),
    (
        "RF-RN-011",
        {
            "titulo_curto": "Logout",
            "descricao": (
                "Botão Sair → POST /api/v1/auth/logout; destruir sessão server-side; "
                "limpar cookie Max-Age=0; FrontEnd retorna ao Login."
            ),
            "aceite": "Recarregar página não restaura acesso autenticado.",
            "prioridade": "Must",
        },
        None,
    ),
    (
        "RF-RN-012",
        {
            "titulo_curto": "Contrato API de autenticação (regras HTTP)",
            "descricao": (
                "Login inválido → 401 login inválido; sessão inválida → 401 Operação não "
                "autorizada; validação senha → 400 RF-RN-007; login OK sem troca → 200 + cookie; "
                "login OK com troca → 200 + change_token sem cookie; troca OK → 200 sem cookie."
            ),
            "aceite": "Contratos conforme Requisitos_Ciclo_Login_MAP.md §9.4.",
            "prioridade": "Must",
        },
        None,
    ),
    (
        "RF-RN-013",
        {
            "titulo_curto": "Cadastro de usuários (somente Administrador)",
            "descricao": (
                "Módulo cadastro acessível só por Administrador (codigo_perfil = 1) via "
                "Configuração (RF-UI-020). BackEnd exige sessão Admin em /api/v1/users/*."
            ),
            "aceite": "Despachante recebe 403 ou UI desabilitada.",
            "prioridade": "Must",
        },
        "Regras de negócio — Cadastro de usuários:",
    ),
    (
        "RF-RN-014",
        {
            "titulo_curto": "Funcionalidades do cadastro de usuários",
            "descricao": (
                "Cadastrar (INSERT + hash 12345 + trocar_senha=1), excluir, editar perfil, "
                "reset senha (RF-RN-015)."
            ),
            "aceite": "CRUD reflete tb_usuario e tb_perfil.",
            "prioridade": "Must",
        },
        None,
    ),
    (
        "RF-RN-015",
        {
            "titulo_curto": "Reset de senha pelo Administrador",
            "descricao": (
                "Reset: UPDATE senha = hash bcrypt de 12345, trocar_senha = 1. Usuário "
                "refaz primeiro acesso."
            ),
            "aceite": "Após reset, senha anterior falha; 12345 exige troca.",
            "prioridade": "Must",
        },
        None,
    ),
    (
        "RF-MAP-RN-001",
        {
            "titulo_curto": "Despachante e CRUD de MAPAS",
            "descricao": (
                "Perfil operacional Despachante; CRUD completo cabeçalho, carros e viagens; "
                "tb_map.id_usuario = sessão; autorização perfil 1 ou 2; não gravar MAPA "
                "em nome de outro usuário."
            ),
            "aceite": "Exclusão respeita FKs sem órfãos.",
            "prioridade": "Must",
        },
        "Regras de negócio — Módulo MAPA:",
    ),
    (
        "RF-MAP-RN-001b",
        {
            "titulo_curto": "Perfis com acesso ao módulo MAPA",
            "descricao": (
                "Autorizados: Administrador (1) e Despachante (2). Operador descontinuado. "
                "API MAPA retorna 403 se codigo_perfil ∉ {1, 2}. Seeds: 1001 Admin, 1002 Despachante."
            ),
            "aceite": "Admin e Despachante acessam Lista_mapa, Cad_mapa e Mapa.",
            "prioridade": "Must",
        },
        None,
    ),
    (
        "RF-MAP-RN-002",
        {
            "titulo_curto": "Listagem (Lista_mapa)",
            "descricao": (
                "Consultar tb_map com JOINs Empresa, Linha, Turno. Ordenação: data DESC, "
                "cod_map DESC."
            ),
            "aceite": "Colunas conforme RF-MAP-UI-002.",
            "prioridade": "Must",
        },
        None,
    ),
    (
        "RF-MAP-RN-003",
        {
            "titulo_curto": "Persistência do cabeçalho (Cad_mapa → tb_map)",
            "descricao": (
                "Inclusão: id_usuario da sessão; validar linha/turno/data/jornadas; gerar "
                "cod_map; INSERT; abrir Mapa. Edição: UPDATE sem alterar cod_map; abrir Mapa. "
                "Cad_mapa não grava tb_item_map nem tb_viagem."
            ),
            "aceite": "Cabeçalho editável; cod_map imutável na edição.",
            "prioridade": "Must",
        },
        None,
    ),
    (
        "RF-MAP-RN-003a",
        {
            "titulo_curto": "Geração automática de cod_map",
            "descricao": (
                "No INSERT: cod_map único 5 dígitos (00001–99999); gerado pelo BackEnd; "
                "imutável após criação; erro se esgotar combinações."
            ),
            "aceite": "Dois MAPAS nunca compartilham o mesmo cod_map.",
            "prioridade": "Must",
        },
        None,
    ),
    (
        "RF-MAP-RN-004",
        {
            "titulo_curto": "Seleção de cadastros mestres",
            "descricao": (
                "Empresa, Linha (filtrada por empresa), Turno, Veículo e Motorista: somente "
                "registros ativo = 1. Inativos não aparecem na UI nem são aceitos via API."
            ),
            "aceite": "Mestres inativos rejeitados.",
            "prioridade": "Must",
        },
        None,
    ),
    (
        "RF-MAP-RN-005",
        {
            "titulo_curto": "Persistência de carros (tb_item_map)",
            "descricao": (
                "N carros por MAPA; idmap = tb_map.id_registro; id_veiculo frota 5 dígitos; "
                "id_motorista de tb_motorista; hor_ini_jor, hor_fim_jor, chegada_ponto DATETIME."
            ),
            "aceite": "CRUD de carros reflete imediatamente na tela Mapa.",
            "prioridade": "Must",
        },
        None,
    ),
    (
        "RF-MAP-RN-006",
        {
            "titulo_curto": "Persistência de viagens (tb_viagem)",
            "descricao": (
                "N viagens por carro; vínculo id_item_registro; horario_saida e "
                "horario_chegada DATETIME; qtd_pas_ida e qtd_pas_volta inteiros ≥ 0."
            ),
            "aceite": "Viagem vinculada a item existente; ambos Qtd persistidos.",
            "prioridade": "Must",
        },
        None,
    ),
    (
        "RF-MAP-RN-007",
        {
            "titulo_curto": "Consulta completa do MAPA",
            "descricao": (
                "Ao abrir Mapa: cabeçalho + empresa/linha/turno/despachante; itens + veículo "
                "+ motorista; viagens por item."
            ),
            "aceite": "Hierarquia map → itens → viagens consistente com banco.",
            "prioridade": "Must",
        },
        None,
    ),
    (
        "RF-MAP-RN-008",
        {
            "titulo_curto": "Exclusão em cascata lógica",
            "descricao": (
                "Excluir MAPA: viagens → itens → cabeçalho. Excluir carro: viagens → item. "
                "Excluir viagem: apenas viagem. Não permitir órfãos."
            ),
            "aceite": "Nenhum órfão em tb_item_map ou tb_viagem.",
            "prioridade": "Must",
        },
        None,
    ),
]


def qname(ns: str, tag: str) -> str:
    return f"{{{NS[ns]}}}{tag}"


def cell_text(cell: ET.Element) -> str:
    return " ".join("".join(cell.itertext()).split())


def find_documented_ids(text_el: ET.Element) -> set[str]:
    """IDs com bloco dedicado (parágrafo-título), não apenas referenciados no texto."""
    documented: set[str] = set()
    for child in text_el:
        if not child.tag.endswith("p"):
            continue
        raw = "".join(child.itertext()).strip().replace("\xa0", " ")
        if ID_RE.fullmatch(raw):
            documented.add(raw)
    return documented


def find_heading_index(children: list[ET.Element], req_id: str) -> int | None:
    for i, child in enumerate(children):
        if child.tag.endswith("p") and child.get(qname("text", "style-name")):
            raw = "".join(child.itertext()).strip()
            if raw == req_id or raw.replace("\xa0", "").startswith(req_id):
                return i
    return None


def find_table_template(children: list[ET.Element]) -> tuple[ET.Element, ET.Element, ET.Element]:
    """Retorna (heading_template, empty_p_template, table_template) de RF-UI-012."""
    for i, child in enumerate(children):
        if not child.tag.endswith("table"):
            continue
        flat = " ".join(cell_text(c) for r in child.findall("table:table-row", NS) for c in r.findall("table:table-cell", NS))
        if "cancelar" in flat.lower() and "login" in flat.lower() and "shell RedMapa" in flat:
            return children[i - 2], children[i - 1], child
    raise RuntimeError("Tabela-modelo RF-UI-012 não encontrada.")


def find_section_template(children: list[ET.Element]) -> ET.Element:
    for child in children:
        if child.tag.endswith("p") and "Interface gráfica" in "".join(child.itertext()):
            return child
    raise RuntimeError("Parágrafo de seção não encontrado.")


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


def remove_rf_ui_013_markdown(text_el: ET.Element) -> bool:
    children = list(text_el)
    start = None
    for i, child in enumerate(children):
        if child.tag.endswith("p") and "RF-UI-013" in "".join(child.itertext()) and "####" in "".join(child.itertext()):
            start = i
            break
    if start is None:
        return False

    end = start + 1
    while end < len(children):
        t = "".join(children[end].itertext()).strip()
        if t == "---" and end > start:
            end += 1
            break
        if end > start + 12:
            break
        end += 1

    for idx in range(end - 1, start - 1, -1):
        text_el.remove(children[idx])
    return True


def insert_nodes(text_el: ET.Element, index: int, nodes: list[ET.Element]) -> None:
    for offset, node in enumerate(nodes):
        text_el.insert(index + offset, node)


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
    heading_tpl, empty_tpl, table_tpl = find_table_template(children)
    section_tpl = find_section_template(children)
    existing = find_documented_ids(text_el)

    # --- 1) RF-UI-013: remover markdown e inserir tabela na ordem correta ---
    rf_ui_013_table_exists = find_heading_index(children, "RF-UI-013") is not None and any(
        "Destino pós-login" in cell_text(c)
        for t in text_el.findall(".//table:table", NS)
        for r in t.findall("table:table-row", NS)
        for c in r.findall("table:table-cell", NS)
    )

    if not rf_ui_013_table_exists:
        removed = remove_rf_ui_013_markdown(text_el)
        children = list(text_el)

        insert_idx = find_heading_index(children, "RF-UI-014")
        if insert_idx is None:
            # fallback: após tabela RF-UI-012
            _, _, tbl = find_table_template(children)
            insert_idx = list(text_el).index(tbl) + 1

        block = build_block(heading_tpl, empty_tpl, table_tpl, "RF-UI-013", RF_UI_013)
        insert_nodes(text_el, insert_idx, block)
        print("RF-UI-013 convertido para tabela (markdown removido)." if removed else "RF-UI-013 tabela inserida.")
    else:
        print("RF-UI-013 já está em formato de tabela.")

    # --- 2) Regras de negócio ---
    documented = find_documented_ids(text_el)
    rn_to_add = [
        (rid, data, section)
        for rid, data, section in BUSINESS_RULES
        if rid not in documented
    ]

    if rn_to_add:
        # Inserir após última tabela RNF-MAP-004
        children = list(text_el)
        insert_idx = None
        for i, child in enumerate(children):
            if child.tag.endswith("p") and "".join(child.itertext()).strip() == "RNF-MAP-004":
                # heading + empty + table + empty
                insert_idx = i + 4
                break
        if insert_idx is None:
            insert_idx = len(children)

        new_nodes: list[ET.Element] = []
        for rid, data, section_title in rn_to_add:
            if section_title:
                new_nodes.append(clone_empty_paragraph(empty_tpl))
                new_nodes.append(clone_section_heading(section_tpl, section_title))
                new_nodes.append(clone_empty_paragraph(empty_tpl))
            new_nodes.extend(build_block(heading_tpl, empty_tpl, table_tpl, rid, data))

        insert_nodes(text_el, insert_idx, new_nodes)
        print(f"Regras de negócio adicionadas: {len(rn_to_add)}")
        for rid, _, _ in rn_to_add:
            print(f"  + {rid}")
    else:
        print("Nenhuma regra de negócio nova a adicionar.")

    new_content = ET.tostring(root, encoding="utf-8", xml_declaration=True)
    temp_odt = ODT_PATH.with_suffix(".tmp.odt")
    with zipfile.ZipFile(ODT_PATH, "r") as zin, zipfile.ZipFile(temp_odt, "w") as zout:
        for item in zin.infolist():
            data = new_content if item.filename == "content.xml" else zin.read(item.filename)
            zout.writestr(item, data)
    temp_odt.replace(ODT_PATH)
    print(f"Atualizado: {ODT_PATH}")
    print(f"Backup: {BACKUP_PATH}")


if __name__ == "__main__":
    main()

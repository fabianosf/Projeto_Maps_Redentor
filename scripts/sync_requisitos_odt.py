# -*- coding: utf-8 -*-
"""
Sincroniza requisitos do Doc_Proj_Map.odt (fonte única).
Usa odt_lib para detectar IDs já documentados no ODT.
"""

from __future__ import annotations

import copy
import re
import shutil
import zipfile
from pathlib import Path
import xml.etree.ElementTree as ET

BASE = Path(__file__).resolve().parents[1]
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from odt_lib import BACKUP_PATH, ID_RE, NS, ODT_PATH, documented_ids

# Ordem de inserção — alinhada ao Doc_Proj_Map.odt (numeração oficial RF-UI-014+)
REQUIREMENTS: list[tuple[str, dict[str, str], str | None]] = [
    (
        "RF-UI-014",
        {
            "titulo_curto": "Botão Cancelar (Cadastro de senha)",
            "descricao": (
                "Ao pressionar Cancelar na tela Cadastro de senha: descartar change_token "
                "em memória; invalidar token no BackEnd; não alterar tb_usuario.senha nem "
                "trocar_senha; fechar tela e retornar ao Login; não criar sessão autenticada."
            ),
            "aceite": (
                "Após Cancelar, trocar_senha permanece 1; próximo acesso exige login com "
                "senha provisória."
            ),
            "prioridade": "Must",
        },
        None,
    ),
    (
        "RF-UI-015",
        {
            "titulo_curto": "Botão Sair (logout)",
            "descricao": (
                "Nas telas autenticadas (Lista_mapa no mínimo), exibir botão Sair que "
                "executa logout conforme RF-RN-011."
            ),
            "aceite": "Após Sair, usuário vê Login; cookie redmapa_sid ausente ou inválido.",
            "prioridade": "Must",
        },
        None,
    ),
    (
        "RF-MAP-UI-001",
        {
            "titulo_curto": "Destino pós-login (MAPA)",
            "descricao": (
                "Após autenticação (Administrador ou Despachante), abrir Lista_mapa."
            ),
            "aceite": (
                "Usuários com codigo_perfil 1 ou 2 acessam a listagem sem ação extra."
            ),
            "prioridade": "Must",
        },
        "Interface gráfica — Módulo MAPA:",
    ),
    (
        "RF-MAP-UI-002",
        {
            "titulo_curto": "Lista_mapa — colunas",
            "descricao": (
                "Exibir colunas Número (cod_map), Empresa, Linha e Turno, com dados de "
                "tb_map e JOINs."
            ),
            "aceite": "Colunas visíveis; dados consistentes com o banco.",
            "prioridade": "Must",
        },
        None,
    ),
    (
        "RF-MAP-UI-003",
        {
            "titulo_curto": "Lista_mapa — seleção",
            "descricao": "Toque em linha abre a tela Mapa do registro selecionado.",
            "aceite": "Navegação com identificador correto do MAPA.",
            "prioridade": "Must",
        },
        None,
    ),
    (
        "RF-MAP-UI-004",
        {
            "titulo_curto": 'Lista_mapa — ícone "+"',
            "descricao": (
                'Ícone "+" no canto superior direito abre Cad_mapa para novo MAPA.'
            ),
            "aceite": "Ícone visível; abre formulário de cabeçalho vazio.",
            "prioridade": "Must",
        },
        None,
    ),
    (
        "RF-MAP-UI-005",
        {
            "titulo_curto": "Cad_mapa — campos do cabeçalho",
            "descricao": (
                "Modos inclusão e edição. Campos: Data, Inijor, Fimjor, Empresa, Linha, "
                "Turno. Despachante da sessão. cod_map automático. Ações Salvar e Cancelar."
            ),
            "aceite": (
                "INSERT/UPDATE apenas em tb_map; cabeçalho editável; cod_map imutável "
                "na edição."
            ),
            "prioridade": "Must",
        },
        None,
    ),
    (
        "RF-MAP-UI-005a",
        {
            "titulo_curto": "Exibição do Número (cod_map)",
            "descricao": (
                "Número do MAPA em 5 dígitos com zeros à esquerda; usuário nunca digita."
            ),
            "aceite": "Código visível na lista após criação do MAPA.",
            "prioridade": "Must",
        },
        None,
    ),
    (
        "RF-MAP-UI-006",
        {
            "titulo_curto": "Mapa — estrutura geral",
            "descricao": (
                "Área superior: carros (tb_item_map). Área inferior: viagens do carro "
                "selecionado. Resumo do cabeçalho com Editar cabeçalho."
            ),
            "aceite": "N carros listados; viagens ao selecionar carro.",
            "prioridade": "Must",
        },
        None,
    ),
    (
        "RF-MAP-UI-007",
        {
            "titulo_curto": "Mapa — carros (tb_item_map)",
            "descricao": (
                "Por carro: Carro (5 dígitos), Matrícula (tb_motorista), Inijor, Fimjor, "
                "Chegada (Ponto). CRUD de carros."
            ),
            "aceite": "Matrícula referencia tb_motorista, não tb_usuario.",
            "prioridade": "Must",
        },
        None,
    ),
    (
        "RF-MAP-UI-008",
        {
            "titulo_curto": "Mapa — viagens (tb_viagem)",
            "descricao": (
                "Por viagem: Saída, Chegada (HH:MM), Qtd ida, Qtd volta. CRUD de viagens."
            ),
            "aceite": "Dois campos Qtd; horários no formato especificado.",
            "prioridade": "Must",
        },
        None,
    ),
    (
        "RF-MAP-UI-009",
        {
            "titulo_curto": "Identidade visual (MAPA)",
            "descricao": (
                "Layout responsivo, bege, Calibri/fallback — alinhado ao RedMapa."
            ),
            "aceite": "Consistência visual com ciclo de login.",
            "prioridade": "Should",
        },
        None,
    ),
    (
        "RF-RN-012",
        {
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
        },
        "Integração — API REST (autenticação):",
    ),
    (
        "RNF-001",
        {
            "titulo_curto": "Senhas em hash bcrypt",
            "descricao": (
                "Senhas nunca persistem em texto puro em tb_usuario.senha; sempre hash bcrypt."
            ),
            "aceite": "Inspeção do banco confirma formato bcrypt.",
            "prioridade": "Must",
        },
        "6.2 Requisitos não funcionais",
    ),
    (
        "RNF-001a",
        {
            "titulo_curto": "Proteção do hash no tráfego",
            "descricao": (
                "Senha digitada trafega entre FrontEnd e BackEnd (HTTPS em produção); "
                "hash nunca retorna ao cliente."
            ),
            "aceite": "Respostas da API não expõem tb_usuario.senha.",
            "prioridade": "Must",
        },
        None,
    ),
    (
        "RNF-001b",
        {
            "titulo_curto": "Algoritmo bcrypt unificado",
            "descricao": (
                "Aplicação externa de cadastro e RedMapa usam o mesmo bcrypt (cost 12)."
            ),
            "aceite": "Hashes compatíveis entre sistemas.",
            "prioridade": "Must",
        },
        None,
    ),
    (
        "RNF-002",
        {
            "titulo_curto": "HTTPS em produção",
            "descricao": "Comunicação Login ↔ API via HTTPS em produção.",
            "aceite": "Certificado TLS ativo em produção.",
            "prioridade": "Must",
        },
        None,
    ),
    (
        "RNF-003",
        {
            "titulo_curto": "Erros genéricos de autenticação",
            "descricao": (
                "Mensagens de erro de autenticação genéricas (anti-enumeração)."
            ),
            "aceite": "Mesma mensagem para matrícula inexistente e senha errada.",
            "prioridade": "Must",
        },
        None,
    ),
    (
        "RNF-004",
        {
            "titulo_curto": "Tempo de resposta do login",
            "descricao": "Tempo de resposta do login < 2 s em LAN de desenvolvimento.",
            "aceite": "Medição em ambiente local.",
            "prioridade": "Should",
        },
        None,
    ),
    (
        "RNF-005",
        {
            "titulo_curto": "Usuários simultâneos (login)",
            "descricao": (
                "Compatibilidade com ~100 usuários simultâneos (pool DB + sessão em memória)."
            ),
            "aceite": "Pool e store dimensionados para carga moderada.",
            "prioridade": "Should",
        },
        None,
    ),
    (
        "RNF-006",
        {
            "titulo_curto": "Cookie de sessão seguro",
            "descricao": (
                "Cookie redmapa_sid: HttpOnly, SameSite=Lax, Secure em produção."
            ),
            "aceite": "Atributos corretos no Set-Cookie.",
            "prioridade": "Must",
        },
        None,
    ),
    (
        "RNF-007",
        {
            "titulo_curto": "TTL de sessão e token",
            "descricao": (
                "Sessão expira após 8 h de inatividade (TTL deslizante); token de troca "
                "de senha expira em 15 min."
            ),
            "aceite": "Expiração verificada em testes.",
            "prioridade": "Must",
        },
        None,
    ),
    (
        "RNF-008",
        {
            "titulo_curto": "Stack da API auth",
            "descricao": "API auth: Flask 3.x; prefixo /api/v1; JSON UTF-8.",
            "aceite": "Endpoints respondem JSON UTF-8.",
            "prioridade": "Must",
        },
        None,
    ),
    (
        "RNF-009",
        {
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
        },
        None,
    ),
    (
        "RNF-MAP-001",
        {
            "titulo_curto": "Responsividade MAPA",
            "descricao": "Layout responsivo; uso em smartphone.",
            "aceite": "Telas utilizáveis em viewport mobile.",
            "prioridade": "Must",
        },
        "Requisitos não funcionais — Módulo MAPA:",
    ),
    (
        "RNF-MAP-002",
        {
            "titulo_curto": "API REST MAPA",
            "descricao": "API REST JSON; BackEnd Python.",
            "aceite": "Integração FrontEnd ↔ API JSON.",
            "prioridade": "Must",
        },
        None,
    ),
    (
        "RNF-MAP-003",
        {
            "titulo_curto": "Formatos de data e hora",
            "descricao": (
                "Banco: DATETIME; UI: DD/MM/AAAA e HH:MM (5 dígitos para hora)."
            ),
            "aceite": "Conversão correta UI ↔ banco.",
            "prioridade": "Must",
        },
        None,
    ),
    (
        "RNF-MAP-004",
        {
            "titulo_curto": "Usuários simultâneos (MAPA)",
            "descricao": "~100 usuários simultâneos.",
            "aceite": "Carga moderada suportada.",
            "prioridade": "Should",
        },
        None,
    ),
]


def qname(ns: str, tag: str) -> str:
    return f"{{{NS[ns]}}}{tag}"


def cell_text(cell: ET.Element) -> str:
    return " ".join("".join(cell.itertext()).split())


def find_existing_ids(text_el: ET.Element) -> set[str]:
    return set(ID_RE.findall("".join(text_el.itertext())))


def find_rf_ui_012_table_index(text_el: ET.Element) -> int:
    children = list(text_el)
    for i, child in enumerate(children):
        if not child.tag.endswith("table"):
            continue
        rows = child.findall("table:table-row", NS)
        if not rows:
            continue
        flat = " ".join(cell_text(c) for r in rows for c in r.findall("table:table-cell", NS))
        if "Botão cancelar(Login)" in flat or "Botao cancelar(Login)" in flat:
            if "Cancelar" in flat and "shell RedMapa" in flat:
                return i
    raise RuntimeError("Tabela RF-UI-012 não encontrada.")


def clone_empty_paragraph(template_p: ET.Element) -> ET.Element:
    p = ET.Element(qname("text", "p"))
    if template_p.get(qname("text", "style-name")):
        p.set(qname("text", "style-name"), template_p.get(qname("text", "style-name")))
    return p


def clone_heading_paragraph(template_heading: ET.Element, req_id: str) -> ET.Element:
    p = copy.deepcopy(template_heading)
    # Substituir texto mantendo estilo
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


def build_requirement_block(
    template_heading: ET.Element,
    template_empty_p: ET.Element,
    template_table: ET.Element,
    req_id: str,
    data: dict[str, str],
) -> list[ET.Element]:
    return [
        clone_empty_paragraph(template_empty_p),
        clone_heading_paragraph(template_heading, req_id),
        clone_empty_paragraph(template_empty_p),
        fill_requirement_table(template_table, data),
        clone_empty_paragraph(template_empty_p),
    ]


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

    existing = find_existing_ids(text_el)
    missing_entries = [(rid, data, sec) for rid, data, sec in REQUIREMENTS if rid not in existing]

    print(f"IDs já presentes no ODT: {len(existing)}")
    print(f"Requisitos a adicionar: {len(missing_entries)}")
    for rid, _, _ in missing_entries:
        print(f"  + {rid}")

    if not missing_entries:
        print("Nada a adicionar.")
        return

    children = list(text_el)
    table_idx = find_rf_ui_012_table_index(text_el)

    # Templates do bloco RF-UI-012
    template_table = children[table_idx]
    template_heading = children[table_idx - 2]  # RF-UI-012
    template_empty_p = children[table_idx - 1]
    template_section = children[253]  # "Interface gráfica (Front End):"

    insert_at = table_idx + 1
    new_nodes: list[ET.Element] = []

    for req_id, data, section_title in missing_entries:
        if section_title:
            new_nodes.append(clone_empty_paragraph(template_empty_p))
            new_nodes.append(clone_section_heading(template_section, section_title))
            new_nodes.append(clone_empty_paragraph(template_empty_p))
        new_nodes.extend(
            build_requirement_block(
                template_heading, template_empty_p, template_table, req_id, data
            )
        )

    for offset, node in enumerate(new_nodes):
        text_el.insert(insert_at + offset, node)

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

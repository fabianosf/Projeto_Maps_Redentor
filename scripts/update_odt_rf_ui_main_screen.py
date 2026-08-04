# -*- coding: utf-8 -*-
"""
Atualiza Doc_Proj_Map.odt — novos RF-UI-013/014/015 (tela principal pós-login),
renumeracao RF-UI-016/017/018, ajustes de conflito e React Native na stack.
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

# --- Novos RF-UI-013, 014, 015 (apos RF-UI-012) ---
NEW_RF_UI_013 = {
    "titulo_curto": "Fechar Login e retornar à tela principal",
    "descricao": (
        "Sempre que o usuário concluir o login **corretamente** (BackEnd confirma autenticação "
        "válida — RF-RN-003) e **não** houver troca obrigatória de senha (`trocar_senha = 0`), "
        "a aplicação deverá: (1) **fechar** a tela/modal de Login; (2) exibir a **tela principal** "
        "(shell RedMapa — RF-UI-002/RF-UI-014) com sessão autenticada. "
        "Se `trocar_senha = 1`, manter fluxo atual: fechar Login e abrir Cadastro de senha (RF-UI-008)."
    ),
    "aceite": (
        "Após login OK sem troca, formulário de Login não permanece visível; usuário vê a tela "
        "principal autenticada. Login inválido não fecha a tela de Login."
    ),
    "prioridade": "Must",
}

NEW_RF_UI_014 = {
    "titulo_curto": "Tela principal — botões de navegação",
    "descricao": (
        "Quando a tela principal estiver exibida **após login autenticado**, além do nome "
        "**RedMapa** (centralizado, RF-UI-002), exibir **três botões** na parte inferior, "
        "lado a lado, com **mesmo layout** (largura, altura, tipografia e estilo): "
        "**Configuração** — abre a tela Configuração; "
        "**Relatório** — abre a tela de Relatórios; "
        "**Mapa** — abre o módulo MAPA (Lista_mapa — RF-UI-016 / RF-MAP-UI-001). "
        "Estética (boas práticas UX/UI): fundo bege (#F5F0E6 ou equivalente); fonte "
        "Calibri/Segoe UI sans-serif 14–16 px; botões com contraste AA (texto escuro sobre "
        "fundo claro ou primária #2563EB com texto branco); área de toque mínima 44×44 px; "
        "espaçamento uniforme entre botões; estado :disabled visível (ex.: cinza #9CA3AF, "
        "cursor not-allowed)."
    ),
    "aceite": (
        "Três botões visíveis, alinhados horizontalmente na margem inferior; toque aciona a "
        "tela correspondente; layout consistente entre os botões."
    ),
    "prioridade": "Must",
}

NEW_RF_UI_015 = {
    "titulo_curto": "Tela principal — perfil Despachante",
    "descricao": (
        "Na tela principal autenticada, se o login foi realizado pelo perfil **Despachante** "
        "(codigo_perfil = 2), o botão **Configuração** deverá permanecer **desabilitado** "
        "(disabled): não clicável, sem navegação à tela Configuração. "
        "Perfil **Administrador** (codigo_perfil = 1): botão Configuração **habilitado**. "
        "Botões Relatório e Mapa permanecem habilitados para ambos os perfis."
    ),
    "aceite": (
        "Despachante: Configuração disabled e inacessível; Admin: Configuração enabled. "
        "Relatório e Mapa acessíveis nos dois perfis."
    ),
    "prioridade": "Must",
}

# --- Antigos 013/014/015 renumerados ---
RF_UI_016 = {
    "titulo_curto": "Botão Mapa — destino Lista_mapa",
    "descricao": (
        "Ao pressionar **Mapa** na tela principal (RF-UI-014), abrir **Lista_mapa** — perfis "
        "Administrador e Despachante. A tela Mapa (detalhe de um MAPA) permanece distinta e "
        "só é aberta após seleção de um registro na lista."
    ),
    "aceite": (
        "Toque em Mapa na tela principal leva à Lista_mapa; detalhe Mapa exige seleção prévia."
    ),
    "prioridade": "Must",
}

RF_UI_017 = {
    "titulo_curto": "Botão Cancelar (Cadastro de senha)",
    "descricao": (
        "Ao pressionar Cancelar na tela Cadastro de senha: descartar change_token em memória; "
        "invalidar token no BackEnd; não alterar tb_usuario.senha nem trocar_senha; fechar "
        "tela e retornar ao Login; não criar sessão autenticada."
    ),
    "aceite": (
        "Após Cancelar, trocar_senha permanece 1; próximo acesso exige login com senha provisória."
    ),
    "prioridade": "Must",
}

RF_UI_018 = {
    "titulo_curto": "Botão Sair (logout)",
    "descricao": (
        "Nas telas autenticadas (tela principal, Lista_mapa, Mapa e demais telas do módulo), "
        "exibir botão **Sair** que executa logout conforme RF-RN-011."
    ),
    "aceite": (
        "Após Sair, usuário retorna à tela principal não autenticada (shell) ou Login; "
        "cookie redmapa_sid ausente ou inválido."
    ),
    "prioridade": "Must",
}

# --- Ajustes em requisitos existentes ---
PATCHES: dict[str, dict[str, str]] = {
    "RF-UI-001": {
        "titulo_curto": "Stack de apresentação",
        "descricao": (
            "A interface deverá ser implementada com **HTML, CSS, JavaScript** e **React Native** "
            "(componentes mobile-first), com layout responsivo, priorizando uso em smartphone. "
            "React Native para telas nativas/híbridas; CSS para tema, tipografia e espaçamento "
            "consistentes com as boas práticas de acessibilidade (contraste, área de toque)."
        ),
        "aceite": (
            "Telas Login, Cadastro de senha, Principal, Configuração, Relatórios e Mapa "
            "utilizáveis em viewport ≥ 360 px, sem scroll horizontal indesejado."
        ),
        "prioridade": "Must",
    },
    "RF-UI-002": {
        "titulo_curto": "Tela principal (shell)",
        "descricao": (
            "Ao abrir o aplicativo, exibir a **tela principal** com: Background bege; nome "
            "**RedMapa** centralizado; fonte Calibri (fallback Segoe UI, sans-serif) 14 pt negrito "
            "preto. **Antes do login:** abrir automaticamente a tela Login (modal/rota/overlay). "
            "**Após login autenticado:** exibir os botões Configuração, Relatório e Mapa na "
            "parte inferior (RF-UI-014). Usuário não autenticado (ex.: após Cancelar no Login — "
            "RF-UI-012) vê apenas shell com nome, sem botões de módulo."
        ),
        "aceite": (
            "Ao carregar a URL, usuário vê RedMapa e Login; após login OK, Login fecha e "
            "shell exibe os três botões inferiores."
        ),
        "prioridade": "Must",
    },
    "RF-UI-008": {
        "titulo_curto": "Navegação pós-login bem sucedido",
        "descricao": (
            "Após Confirmar no Login, a UI só avança se o BackEnd confirmar autenticação válida "
            "(RF-RN-003), nesta ordem: "
            "(1) Validar matrícula + senha (incluindo senha provisória 12345 no primeiro acesso); "
            "(2) Se autenticação OK e trocar_senha = 1 → fechar Login e abrir Cadastro de senha; "
            "(3) Se autenticação OK e trocar_senha = 0 → fechar Login e exibir tela principal "
            "autenticada com botões (RF-UI-013, RF-UI-014) — **não** abrir Lista_mapa "
            "automaticamente."
        ),
        "aceite": (
            "Usuário com trocar_senha = 1 não abre Cadastro de senha sem senha provisória "
            "correta; senha errada exibe RF-UI-007. Usuário com trocar_senha = 0 chega à "
            "tela principal, não diretamente à Lista_mapa."
        ),
        "prioridade": "Must",
    },
    "RF-MAP-UI-001": {
        "titulo_curto": "Acesso ao módulo MAPA (botão Mapa)",
        "descricao": (
            "Após autenticação (Administrador ou Despachante), o módulo MAPA é acessado pelo "
            "botão **Mapa** na tela principal (RF-UI-014), que abre **Lista_mapa**. "
            "Não há abertura automática da Lista_mapa imediatamente após o login."
        ),
        "aceite": (
            "Usuários com codigo_perfil 1 ou 2 acessam Lista_mapa ao pressionar Mapa na "
            "tela principal."
        ),
        "prioridade": "Must",
    },
}

FRONTEND_ARCH_PATCH = (
    "HTML5, CSS3, JavaScript (ES6+) e React Native (componentes mobile-first); "
    "fetch com credentials: include; tema bege, Calibri/Segoe UI, botões com contraste AA."
)


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


def fill_requirement_table(table: ET.Element, data: dict[str, str]) -> None:
    for row in table.findall("table:table-row", NS):
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


def find_req_table_index(text_el: ET.Element, req_id: str) -> int:
    children = list(text_el)
    for i, child in enumerate(children):
        if child.tag != qname("text", "p"):
            continue
        t = cell_text(child) if False else " ".join("".join(child.itertext()).split())
        if t.strip() == req_id:
            for j in range(i + 1, min(i + 5, len(children))):
                if children[j].tag == qname("table", "table"):
                    return j
    raise RuntimeError(f"Tabela de {req_id} não encontrada.")


def rename_req_heading(text_el: ET.Element, old_id: str, new_id: str) -> None:
    for child in text_el.findall("text:p", NS):
        t = " ".join("".join(child.itertext()).split())
        if t.strip() == old_id:
            for sub in list(child):
                child.remove(sub)
            child.text = new_id
            return
    raise RuntimeError(f"Cabeçalho {old_id} não encontrado.")


def clone_empty_paragraph(template_p: ET.Element) -> ET.Element:
    p = ET.Element(qname("text", "p"))
    if template_p.get(qname("text", "style-name")):
        p.set(qname("text", "style-name"), template_p.get(qname("text", "style-name")))
    return p


def clone_heading(template: ET.Element, req_id: str) -> ET.Element:
    p = copy.deepcopy(template)
    for child in list(p):
        p.remove(child)
    p.text = req_id
    return p


def build_block(template_heading, template_empty, template_table, req_id, data):
    tbl = copy.deepcopy(template_table)
    fill_requirement_table(tbl, data)
    return [
        clone_empty_paragraph(template_empty),
        clone_heading(template_heading, req_id),
        clone_empty_paragraph(template_empty),
        tbl,
        clone_empty_paragraph(template_empty),
    ]


def patch_arch_frontend_table(text_el: ET.Element) -> None:
    for child in list(text_el):
        if child.tag != qname("table", "table"):
            continue
        flat = " ".join(cell_text(c) for r in child.findall("table:table-row", NS) for c in r.findall("table:table-cell", NS))
        if "HTML5" in flat and "JavaScript" in flat and "FrontEnd" in flat or (
            "HTML5" in flat and "mobile-first" in flat.lower() and "Tecnologia" in flat
        ):
            for row in child.findall("table:table-row", NS):
                cells = row.findall("table:table-cell", NS)
                if len(cells) < 2:
                    continue
                row_text = cell_text(cells[0]) + cell_text(cells[1])
                if row_text.startswith("JavaScript") or "JavaScript (ES6" in row_text:
                    set_cell_text_preserve_style(
                        cells[1] if len(cells) > 1 else cells[0],
                        FRONTEND_ARCH_PATCH.split(";")[0].strip()
                        if len(cells) == 2
                        else FRONTEND_ARCH_PATCH,
                    )
            # add React Native row if 3-col tech table
            cols = child.findall("table:table-column", NS)
            if len(cols) >= 2:
                rows = child.findall("table:table-row", NS)
                if rows and "React Native" not in flat:
                    proto = rows[-1]
                    new_row = copy.deepcopy(proto)
                    cells = new_row.findall("table:table-cell", NS)
                    if len(cells) == 3:
                        set_cell_text_preserve_style(cells[0], "React Native")
                        set_cell_text_preserve_style(
                            cells[1],
                            "Componentes mobile-first (telas Login, Principal, MAPA)",
                        )
                        set_cell_text_preserve_style(cells[2], "")
                        child.append(new_row)
            return


def main() -> None:
    if not ODT_PATH.exists():
        raise FileNotFoundError(ODT_PATH)

    shutil.copy2(ODT_PATH, BACKUP_PATH)

    with zipfile.ZipFile(ODT_PATH, "r") as zin:
        content = zin.read("content.xml")
        archive = {i.filename: zin.read(i.filename) for i in zin.infolist()}

    root = ET.fromstring(content)
    text_el = root.find(".//office:text", NS)
    if text_el is None:
        raise RuntimeError("office:text não encontrado")

    children = list(text_el)
    t12 = find_req_table_index(text_el, "RF-UI-012")
    template_heading = children[t12 - 2]
    template_empty = children[t12 - 1]
    template_table = children[t12]

    # 1) Substituir conteudo RF-UI-013, 014, 015 pelos novos
    for req_id, data in [
        ("RF-UI-013", NEW_RF_UI_013),
        ("RF-UI-014", NEW_RF_UI_014),
        ("RF-UI-015", NEW_RF_UI_015),
    ]:
        idx = find_req_table_index(text_el, req_id)
        fill_requirement_table(children[idx], data)
        print(f"Atualizado {req_id}")

    # 2) Patches RF-UI-001, 002, 008, RF-MAP-UI-001
    for req_id, data in PATCHES.items():
        idx = find_req_table_index(text_el, req_id)
        fill_requirement_table(list(text_el)[idx], data)
        print(f"Patch {req_id}")

    # 3) Inserir RF-UI-016, 017, 018 apos bloco RF-UI-015
    t15 = find_req_table_index(text_el, "RF-UI-015")
    insert_at = t15 + 1
    new_nodes = []
    for req_id, data in [
        ("RF-UI-016", RF_UI_016),
        ("RF-UI-017", RF_UI_017),
        ("RF-UI-018", RF_UI_018),
    ]:
        new_nodes.extend(
            build_block(template_heading, template_empty, template_table, req_id, data)
        )

    for offset, node in enumerate(new_nodes):
        text_el.insert(insert_at + offset, node)
    print("Inseridos RF-UI-016, RF-UI-017, RF-UI-018")

    # 4) Arquitetura — React Native na tabela FrontEnd
    patch_arch_frontend_table(text_el)
    print("Arquitetura FrontEnd: React Native")

    archive["content.xml"] = ET.tostring(root, encoding="utf-8", xml_declaration=True)
    temp = ODT_PATH.with_suffix(".tmp.odt")
    with zipfile.ZipFile(temp, "w", compression=zipfile.ZIP_DEFLATED) as zout:
        for name, data in archive.items():
            zout.writestr(name, data)
    temp.replace(ODT_PATH)
    print(f"Salvo: {ODT_PATH}")
    print(f"Backup: {BACKUP_PATH}")


if __name__ == "__main__":
    main()

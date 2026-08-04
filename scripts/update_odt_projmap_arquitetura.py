# -*- coding: utf-8 -*-
"""
Atualiza Doc_Proj_Map.odt:
  - Substitui seção 3 (Projeto SEDA) por 3. Projeto ProjMap (introdução)
  - Insere capítulo 4. Arquitetura (conteúdo de Doc/Arquitetura.md)
  - Atualiza índice e renomeia seção Interface gráfica para 5.)
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
ARCH_IMAGE_SRC = BASE / "Doc" / "images" / "redmapa-arquitetura.png"
ARCH_IMAGE_ODT = "Pictures/redmapa-arquitetura.png"

NS = {
    "office": "urn:oasis:names:tc:opendocument:xmlns:office:1.0",
    "text": "urn:oasis:names:tc:opendocument:xmlns:text:1.0",
    "table": "urn:oasis:names:tc:opendocument:xmlns:table:1.0",
    "draw": "urn:oasis:names:tc:opendocument:xmlns:drawing:1.0",
    "svg": "urn:oasis:names:tc:opendocument:xmlns:svg-compatible:1.0",
    "xlink": "http://www.w3.org/1999/xlink",
}

SECTION3_PARAGRAPHS = [
    (
        "O ProjMap (RedMapa — Sistema Eletrônico de MAPAS Operacionais) é uma aplicação WEB "
        "mobile-first desenvolvida para o Grupo Redentor, com o propósito de digitalizar e "
        "modernizar a gestão operacional da frota de ônibus nos consórcios Transcarioca, "
        "Intersul e Santa Cruz."
    ),
    (
        "O sistema substitui o processo manual de elaboração e consulta de MAPAS — documentos "
        "operacionais que registram, para cada dia e turno, a escala de veículos, motoristas e "
        "viagens de uma linha — permitindo que despachantes e administradores trabalhem "
        "diretamente em smartphones ou tablets, no pátio ou em campo."
    ),
    (
        "O objetivo principal do ProjMap é centralizar, em uma única plataforma, o ciclo "
        "completo de um MAPA: cadastro do cabeçalho (data, jornada, empresa, linha e turno), "
        "manutenção dos carros alocados e registro das viagens de cada veículo, com persistência "
        "confiável, controle de acesso por perfil e interface adaptada ao uso móvel."
    ),
    (
        "O público-alvo são colaboradores do setor de Tráfego — em especial despachantes "
        "(perfil operacional) e administradores (perfil de gestão). O acesso é individualizado "
        "por matrícula e senha; no primeiro login o usuário deve cadastrar senha definitiva, "
        "substituindo a senha provisória definida no cadastro interno (Administrador)."
    ),
    (
        "Principais funcionalidades — Autenticação: login por matrícula e senha, troca "
        "obrigatória de senha no primeiro acesso, sessão autenticada via cookie HttpOnly "
        "(redmapa_sid) e logout explícito que invalida a sessão no servidor."
    ),
    (
        "Lista de MAPAS (Lista_mapa): visualização tabular dos MAPAS cadastrados — número "
        "(cod_map), empresa, linha e turno — com seleção de registro para edição e ícone "
        '"+" para inclusão de novo MAPA.'
    ),
    (
        "Cadastro de MAPA (Cad_mapa): formulário de cabeçalho em modo inclusão ou edição, "
        "com geração automática do código numérico do MAPA (cinco dígitos), campos de data, "
        "início e fim de jornada, empresa, linha, turno e despachante vinculado à sessão."
    ),
    (
        "Tela Mapa: área superior com listagem de carros (itens do MAPA) e área inferior com "
        "viagens do carro selecionado; permite editar cabeçalho, incluir/alterar/excluir carros "
        "e viagens conforme as regras de negócio do módulo MAPA."
    ),
    (
        "Perfis de acesso: Administrador (codigo_perfil = 1) e Despachante (codigo_perfil = 2). "
        "Ambos acessam o módulo MAPA após autenticação; demais perfis e autorizações "
        "complementares seguem especificação nos capítulos de Requisitos e Regras de Negócio."
    ),
    (
        "Stack tecnológica (visão resumida): FrontEnd estático HTML, CSS e JavaScript consome "
        "API REST JSON implementada em Python (Flask); dados persistidos em MariaDB (banco map). "
        "Configurações sensíveis de conexão são armazenadas de forma criptografada (Fernet) "
        "em arquivos .dat protegidos por chave externa ao repositório."
    ),
    (
        "Estado de evolução: o BackEnd de autenticação (/api/v1/auth/*), a camada de acesso a "
        "dados (DAL) e o modelo relacional do banco já estão implementados; as telas de interface "
        "e os endpoints REST do módulo MAPA seguem especificação detalhada neste documento."
    ),
    (
        "Cadastro de usuários: realizado na própria aplicação RedMapa — perfil Administrador "
        "acessa a tela Configuração; BackEnd persiste em tb_usuario via API REST (/api/v1), "
        "com senha inicial bcrypt de 12345 e trocar_senha = 1."
    ),
    (
        "Convenções: RedMapa é o nome da aplicação; PROJ_MAP identifica o repositório e o "
        "projeto de desenvolvimento; MAPA (maiúsculas) designa o documento operacional "
        "gerenciado pelo sistema. Detalhes de arquitetura, deploy e segurança encontram-se "
        "no capítulo 4 deste documento."
    ),
]

ARCH_ASCII_DIAGRAM = [
    "┌─────────────────┐     HTTPS/JSON      ┌──────────────────────┐     SQL      ┌─────────────┐",
    "│  Cliente WEB    │ ◄─────────────────► │  BackEnd Python      │ ◄──────────► │  MariaDB    │",
    "│  (browser)      │   cookie HttpOnly   │  Flask + DAL         │   pymysql    │  banco map  │",
    "└─────────────────┘                     └──────────────────────┘              └─────────────┘",
    "                                                │",
    "                                                │ sessão em memória",
    "                                                ▼",
    "                                        SessionStore (processo)",
]

FOLDER_TREE = [
    "PROJ_MAP/",
    "├── DAL/arquivos_crip                    # Configurações criptografadas (.dat) e chave Fernet",
    "├── database/                # DDL, seeds, migrações SQL",
    "├── Doc/                     # Documentação (requisitos, DDL, arquitetura)",
    "├── BackEnd/                 # BackEnd Flask",
    "│   ├── app.py               # Entry point Flask",
    "│   ├── auth_routes.py       # Rotas /api/v1/auth/*",
    "│   ├── auth_service.py      # Lógica de login e troca de senha",
    "│   ├── auth_session.py      # Cookie e helpers de sessão",
    "│   ├── session_store.py     # Store de sessão e tokens em memória",
    "│   ├── DAL.py               # Data Access Layer",
    "│   └── CONFIGURACAO.py      # Leitura de configs criptografadas",
    "├── scripts/                 # Scripts PowerShell (setup MariaDB, configs)",
    "├── PROJ_GAC/                # Utilitário legado de configuração (referência)",
    "└── requirements.txt         # Dependências Python",
]

DATA_HIERARCHY = [
    "tb_usuario / tb_perfil          (autenticação e perfis)",
    "tb_empresa, tb_linha, tb_turno  (cadastros mestres)",
    "tb_motorista, tb_veiculo        (cadastros operacionais)",
    "",
    "tb_map                          (cabeçalho do MAPA)",
    "  └── tb_item_map               (carros / itens)",
    "        └── tb_viagem           (viagens por carro)",
]

LOCAL_EXEC = [
    "# Dependências",
    "python -m pip install -r requirements.txt",
    "",
    "# BackEnd (API)",
    "python -m BackEnd.app",
    "",
    "# Banco — ver database/README.md",
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


def build_2col_table(template: ET.Element, header: tuple[str, str], rows: list[tuple[str, str]]) -> ET.Element:
    tbl = copy.deepcopy(template)
    data_rows = tbl.findall("table:table-row", NS)
    proto_header, proto_data = data_rows[0], data_rows[1]
    for row in data_rows:
        tbl.remove(row)
    hdr = copy.deepcopy(proto_header)
    cells = hdr.findall("table:table-cell", NS)
    set_cell_text(cells[0], header[0])
    set_cell_text(cells[1], header[1])
    tbl.append(hdr)
    for a, b in rows:
        row = copy.deepcopy(proto_data)
        cells = row.findall("table:table-cell", NS)
        set_cell_text(cells[0], a)
        set_cell_text(cells[1], b)
        tbl.append(row)
    return tbl


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


def clone_image_paragraph(
    template_p: ET.Element,
    href: str,
    width_cm: str = "17cm",
    height_cm: str = "11.33cm",
    fig_name: str = "FiguraArquitetura",
) -> ET.Element:
    p = copy.deepcopy(template_p)
    frame = p.find("draw:frame", NS)
    if frame is None:
        raise RuntimeError("Parágrafo template não contém draw:frame")
    frame.set(qname("draw", "name"), fig_name)
    frame.set(qname("svg", "width"), width_cm)
    frame.set(qname("svg", "height"), height_cm)
    img = frame.find("draw:image", NS)
    if img is None:
        raise RuntimeError("Frame sem draw:image")
    img.set(qname("xlink", "href"), href)
    return p


def find_paragraph_index(text_el: ET.Element, predicate) -> int:
    for i, child in enumerate(list(text_el)):
        if child.tag == qname("text", "p") and predicate(para_text(child)):
            return i
    raise RuntimeError("Parágrafo não encontrado")


def build_section_3(templates: dict) -> list[ET.Element]:
    nodes: list[ET.Element] = [
        clone_heading(templates["chapter"], "3. Projeto ProjMap"),
        make_paragraph("P85"),
    ]
    for paragraph in SECTION3_PARAGRAPHS:
        nodes.append(make_paragraph("P87", paragraph))
        nodes.append(make_paragraph("P88"))
    nodes.append(make_paragraph("P85"))
    return nodes


def build_architecture_chapter(templates: dict) -> list[ET.Element]:
    ch = templates["chapter"]
    sub = templates["subsection"]
    body = "P87"
    gap = "P88"
    empty = "P85"
    t2 = templates["table2"]
    t3 = templates["table3"]

    nodes: list[ET.Element] = [
        clone_heading(ch, "4. Arquitetura"),
        make_paragraph(empty),
        build_2col_table(
            t2,
            ("Campo", "Valor"),
            [
                ("Projeto", "RedMapa (MAP) — gestão operacional de frota de ônibus"),
                ("Tipo", "Aplicação WEB mobile-first"),
                ("Versão do documento", "1.0"),
                ("Data", "20 de julho de 2026"),
            ],
        ),
        make_paragraph(gap),
        make_paragraph(
            body,
            "Documento exclusivo de arquitetura. Requisitos funcionais detalhados encontram-se "
            "nos capítulos de Requisitos deste documento e em Doc/Requisitos_Ciclo_Login_MAP.md "
            "e Doc/Requisitos_Modulo_Mapa_MAP.md.",
        ),
        make_paragraph(gap),
        clone_heading(sub, "4.1 Visão geral"),
        make_paragraph(empty),
        make_paragraph(
            body,
            "O RedMapa segue uma arquitetura cliente-servidor em camadas, com FrontEnd estático "
            "(HTML/CSS/JS) consumindo uma API REST JSON implementada em Python (Flask), "
            "persistindo dados em MariaDB.",
        ),
        make_paragraph(gap),
    ]
    for line in ARCH_ASCII_DIAGRAM:
        nodes.append(make_paragraph(body, line))
    nodes.extend(
        [
            make_paragraph(gap),
            clone_image_paragraph(
                templates["image_p"],
                ARCH_IMAGE_ODT,
                fig_name="FiguraArquiteturaRedMapa",
            ),
            make_paragraph(gap),
            clone_heading(sub, "4.2 Sistema operacional e ambiente"),
            make_paragraph(empty),
            build_2col_table(
                t2,
                ("Aspecto", "Especificação"),
                [
                    ("SO de desenvolvimento", "Microsoft Windows 10/11 (ambiente atual do projeto)"),
                    ("SO de produção (alvo)", "Linux (VPS) ou Windows Server — a definir no deploy"),
                    ("Shell / automação", "PowerShell (scripts/setup_mariadb.ps1, scripts/reinstalar_mariadb.ps1)"),
                    ("Runtime Python", "Python 3.11+"),
                    ("Servidor de banco", "MariaDB 12.x"),
                    ("Ambiente local", "localhost — API na porta 5000, MariaDB na porta 3306"),
                ],
            ),
            make_paragraph(gap),
            clone_heading(sub, "4.3 Stack tecnológica"),
            make_paragraph(empty),
            clone_heading(sub, "4.3.1 FrontEnd (planejado / em especificação)"),
            make_paragraph(empty),
            build_3col_table(
                t3,
                ("Tecnologia", "Uso", "Observação"),
                [
                    ("HTML5", "Estrutura das telas", ""),
                    ("CSS3", "Layout responsivo, mobile-first", ""),
                    ("JavaScript (ES6+)", "Interação, chamadas à API (fetch com credentials: 'include')", ""),
                    ("Fonte", "Calibri (fallback: Segoe UI, sans-serif)", ""),
                ],
            ),
            make_paragraph(gap),
            make_paragraph(
                body,
                "O FrontEnd ainda não possui pasta dedicada no repositório; a stack está definida "
                "nos requisitos de interface.",
            ),
            make_paragraph(gap),
            clone_heading(sub, "4.3.2 BackEnd (implementado)"),
            make_paragraph(empty),
            build_3col_table(
                t3,
                ("Tecnologia", "Versão", "Uso"),
                [
                    ("Python", "3.11+", "Linguagem principal"),
                    ("Flask", "≥ 3.0", "Servidor HTTP, rotas REST, JSON"),
                    ("bcrypt", "≥ 4.1", "Hash e validação de senhas (cost 12)"),
                    ("pandas", "≥ 2.0", "Resultados de consultas SQL via DAL"),
                    ("pymysql", "≥ 1.1", "Driver MariaDB/MySQL"),
                    ("psycopg2-binary", "≥ 2.9", "Driver PostgreSQL (suporte alternativo no DAL)"),
                    ("cryptography (Fernet)", "≥ 42.0", "Descriptografia de arquivos .dat de configuração"),
                ],
            ),
            make_paragraph(gap),
            clone_heading(sub, "4.3.3 Banco de dados"),
            make_paragraph(empty),
            build_2col_table(
                t2,
                ("Tecnologia", "Uso"),
                [
                    ("MariaDB", "SGBD principal — banco map"),
                    ("PostgreSQL", "Suporte opcional via DAL (schema_postgresql.sql, DAL/arquivos_cripmap_PostGree.dat)"),
                    ("SQL", "DDL em database/schema.sql, migrações em database/schema_migrate_*.sql"),
                ],
            ),
            make_paragraph(gap),
            clone_heading(sub, "4.4 Camadas da aplicação"),
            make_paragraph(empty),
            build_3col_table(
                t3,
                ("Camada", "Responsabilidade", "Artefatos"),
                [
                    ("Apresentação", "Telas WEB, UX mobile-first", "(a implementar) HTML/CSS/JS"),
                    ("API / Controlador", "Endpoints REST, cookies HTTP, status codes", "BackEnd/app.py, BackEnd/auth_routes.py"),
                    ("Serviço / Domínio", "Regras de autenticação, validações", "BackEnd/auth_service.py"),
                    ("Sessão", "Estado autenticado server-side", "BackEnd/session_store.py, BackEnd/auth_session.py"),
                    ("Acesso a dados", "Pool de conexões, queries, cache, circuit breaker", "BackEnd/DAL.py"),
                    ("Configuração", "Parâmetros criptografados de conexão", "BackEnd/CONFIGURACAO.py, DAL/arquivos_crip*.dat, DAL/arquivos_cripchave.key"),
                    ("Persistência", "Tabelas relacionais", "MariaDB — ver Doc/DDL_Banco_MAP.md"),
                ],
            ),
            make_paragraph(gap),
            clone_heading(sub, "4.5 Estrutura de pastas do repositório"),
            make_paragraph(empty),
        ]
    )
    for line in FOLDER_TREE:
        nodes.append(make_paragraph(body, line))
    nodes.extend(
        [
            make_paragraph(gap),
            clone_heading(sub, "4.6 Comunicação entre componentes"),
            make_paragraph(empty),
            clone_heading(sub, "4.6.1 Protocolo"),
            make_paragraph(empty),
            build_3col_table(
                t3,
                ("Trecho", "Protocolo", "Formato"),
                [
                    ("Browser ↔ API", "HTTP/HTTPS", "JSON (Content-Type: application/json)"),
                    ("API ↔ MariaDB", "TCP (porta 3306)", "SQL parametrizado via pymysql"),
                    ("Cadastro usuários (Admin) ↔ API RedMapa", "HTTPS/JSON", "INSERT em tb_usuario via BackEnd (bcrypt)"),
                ],
            ),
            make_paragraph(gap),
            clone_heading(sub, "4.6.2 Prefixo da API"),
            make_paragraph(empty),
            make_paragraph(body, "Base: /api/v1"),
            make_paragraph(body, "Autenticação: /api/v1/auth/*"),
            make_paragraph(body, "Saúde: /api/v1/health"),
            make_paragraph(body, "Módulo MAPA: /api/v1/... (a implementar)"),
            make_paragraph(gap),
            clone_heading(sub, "4.6.3 Autenticação e sessão"),
            make_paragraph(empty),
            build_2col_table(
                t2,
                ("Mecanismo", "Descrição"),
                [
                    ("Sessão autenticada", "Server-side em memória; cookie redmapa_sid (HttpOnly, SameSite=Lax)"),
                    ("TTL da sessão", "8 horas, renovação deslizante a cada request"),
                    ("Primeiro acesso", "Token change_token (15 min) no corpo JSON — sem cookie de sessão"),
                    ("Produção", "REDMAPA_COOKIE_SECURE=true (cookie Secure em HTTPS)"),
                ],
            ),
            make_paragraph(gap),
            clone_heading(sub, "4.7 Modelo de dados (visão arquitetural)"),
            make_paragraph(empty),
        ]
    )
    for line in DATA_HIERARCHY:
        nodes.append(make_paragraph(body, line) if line else make_paragraph(gap))
    nodes.extend(
        [
            make_paragraph(gap),
            make_paragraph(
                body,
                "Convenção: chaves estrangeiras referenciam PK (id_*); códigos de negócio (cod_*) são UNIQUE. "
                "Documentação completa: Doc/DDL_Banco_MAP.md.",
            ),
            make_paragraph(gap),
            clone_heading(sub, "4.8 Cadastro de usuários e utilitários"),
            make_paragraph(empty),
            build_3col_table(
                t3,
                ("Sistema", "Relação", "Integração"),
                [
                    (
                        "Cadastro de usuários (RedMapa)",
                        "Administrador cadastra em tb_usuario",
                        "Tela Configuração → API /api/v1; bcrypt 12345; perfil Admin",
                    ),
                    (
                        "PROJ_GAC",
                        "Utilitário legado de geração de configs",
                        "Mesmo padrão Fernet (DAL/arquivos_cripchave.key); referência histórica",
                    ),
                ],
            ),
            make_paragraph(gap),
            clone_heading(sub, "4.9 Segurança (visão arquitetural)"),
            make_paragraph(empty),
            build_2col_table(
                t2,
                ("Aspecto", "Abordagem"),
                [
                    ("Senhas", "bcrypt cost 12; nunca armazenadas em texto puro"),
                    ("Configurações DB", "Arquivos .dat criptografados com Fernet; chave.key fora do Git (.gitignore)"),
                    ("Sessão", "Cookie HttpOnly; ID opaco (secrets.token_urlsafe); store server-side"),
                    ("Transporte", "HTTPS obrigatório em produção"),
                    ("Mensagens de erro", "Genéricas no login (anti-enumeração)"),
                    ("Autorização", "Perfil na sessão (codigo_perfil: Administrador=1, Despachante=2)"),
                ],
            ),
            make_paragraph(gap),
            clone_heading(sub, "4.10 Disponibilidade e escala"),
            make_paragraph(empty),
            build_2col_table(
                t2,
                ("Aspecto", "Decisão atual"),
                [
                    ("Usuários simultâneos", "~100 (requisito Should)"),
                    ("Pool de conexões DB", "Até 10 conexões (ConnectionPool no DAL)"),
                    ("Sessões", "Em memória do processo Flask (reinício invalida sessões)"),
                    ("Cache de queries", "TTL 300 s no DAL (QueryCache)"),
                    ("Resiliência DB", "Circuit breaker no DAL (5 falhas → OPEN por 30 s)"),
                ],
            ),
            make_paragraph(gap),
            make_paragraph(
                body,
                "Para múltiplas instâncias do BackEnd em produção, será necessário store de sessão "
                "compartilhado (ex.: Redis) — evolução futura, não implementada.",
            ),
            make_paragraph(gap),
            clone_heading(sub, "4.11 Deploy (visão alvo)"),
            make_paragraph(empty),
            build_2col_table(
                t2,
                ("Componente", "Opção de hospedagem"),
                [
                    ("FrontEnd estático", "CDN / Vercel / Nginx"),
                    ("BackEnd Flask", "VPS Linux (Gunicorn/uWSGI + Nginx) ou Windows Server"),
                    ("MariaDB", "Mesmo VPS ou servidor dedicado"),
                ],
            ),
            make_paragraph(gap),
            make_paragraph(
                body,
                "Estudo preliminar de FrontEnd na Vercel: Doc/Relatorio_Plataforma_Vercel.md. "
                "O BackEnd Python com sessão server-side e MariaDB não é candidato natural à "
                "Vercel serverless sem adaptações.",
            ),
            make_paragraph(gap),
            clone_heading(sub, "4.12 Variáveis de ambiente"),
            make_paragraph(empty),
            build_3col_table(
                t3,
                ("Variável", "Padrão", "Descrição"),
                [
                    ("REDMAPA_CONFIG", "map_MariaDB.dat", "Arquivo de configuração em DAL/arquivos_crip"),
                    ("REDMAPA_HOST", "0.0.0.0", "Host do servidor Flask"),
                    ("REDMAPA_PORT", "5000", "Porta da API"),
                    ("REDMAPA_COOKIE_SECURE", "false", "true em produção (HTTPS)"),
                    ("FLASK_DEBUG", "0", "1 apenas em desenvolvimento"),
                ],
            ),
            make_paragraph(gap),
            clone_heading(sub, "4.13 Execução local"),
            make_paragraph(empty),
        ]
    )
    for line in LOCAL_EXEC:
        nodes.append(make_paragraph(body, line) if line else make_paragraph(gap))
    nodes.extend(
        [
            build_2col_table(
                t2,
                ("Serviço", "URL / Host"),
                [
                    ("API", "http://localhost:5000/api/v1"),
                    ("Health check", "http://localhost:5000/api/v1/health"),
                    ("MariaDB", "localhost:3306 — banco map"),
                ],
            ),
            make_paragraph(gap),
            clone_heading(sub, "4.14 Documentos relacionados"),
            make_paragraph(empty),
            build_2col_table(
                t2,
                ("Documento", "Conteúdo"),
                [
                    ("Doc/Requisitos_Ciclo_Login_MAP.md", "Requisitos e API de autenticação"),
                    ("Doc/Requisitos_Modulo_Mapa_MAP.md", "Requisitos do módulo MAPA"),
                    ("Doc/DDL_Banco_MAP.md", "Modelo de dados detalhado"),
                    ("database/README.md", "Setup do banco MariaDB"),
                ],
            ),
            make_paragraph(gap),
            make_paragraph(body, "Documento de arquitetura do projeto PROJ_MAP / RedMapa."),
            make_paragraph(empty),
        ]
    )
    return nodes


def update_index_table(table_el: ET.Element) -> None:
    rows = table_el.findall("table:table-row", NS)
    if len(rows) < 2:
        return

    entries: list[list[str]] = []
    for row in rows[1:]:
        cells = row.findall("table:table-cell", NS)
        if len(cells) < 3:
            continue
        entries.append(
            [para_text(cells[0]), para_text(cells[1]), para_text(cells[2])]
        )

    updated: list[list[str]] = []
    for _cod, desc, pag in entries:
        upper = desc.upper()
        if "ARQUITETURA" in upper:
            continue
        if "PROJETO SEDA" in upper or "O PROJETO SEDA" in upper:
            desc = "3. PROJETO PROJMAP"
        elif upper.startswith("4.") and "INTERFACE" in upper:
            desc = "5. INTERFACE GRÁFICA"
        elif upper.startswith("5.") and "REGRAS" in upper:
            desc = "6. REGRAS DE NEGÓCIO"
        elif (
            upper.startswith("6.")
            and "REQUISITOS" in upper
            and "FUNCIONAIS" not in upper
            and "NÃO" not in upper
            and "NAO" not in upper
        ):
            desc = "7. REQUISITOS"
        elif upper.startswith("7.") and "SERVIDOR" in upper:
            desc = "8. SERVIDOR"
        updated.append([_cod, desc, pag])

    for i, entry in enumerate(updated):
        if "PROJMAP" in entry[1].upper():
            updated.insert(i + 1, ["", "4. ARQUITETURA", "07"])
            break

    for i, entry in enumerate(updated, start=1):
        entry[0] = f"{i:02d}"

    proto = rows[1]
    for row in rows[1:]:
        table_el.remove(row)

    for cod, desc, pag in updated:
        row = copy.deepcopy(proto)
        cells = row.findall("table:table-cell", NS)
        set_cell_text(cells[0], cod)
        set_cell_text(cells[1], desc)
        set_cell_text(cells[2], pag)
        table_el.append(row)


def add_manifest_entry(manifest_xml: bytes, path: str) -> bytes:
    if path.encode() in manifest_xml or path.split("/", 1)[-1].encode() in manifest_xml:
        return manifest_xml
    root = ET.fromstring(manifest_xml)
    ns = "urn:oasis:names:tc:opendocument:xmlns:manifest:1.0"
    entry = ET.Element(f"{{{ns}}}file-entry")
    entry.set(f"{{{ns}}}full-path", path)
    entry.set(f"{{{ns}}}media-type", "image/png")
    root.append(entry)
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def main() -> None:
    if not ODT_PATH.exists():
        raise FileNotFoundError(ODT_PATH)
    if not ARCH_IMAGE_SRC.exists():
        raise FileNotFoundError(ARCH_IMAGE_SRC)

    shutil.copy2(ODT_PATH, BACKUP_PATH)

    with zipfile.ZipFile(ODT_PATH, "r") as zin:
        content = zin.read("content.xml")
        manifest = zin.read("META-INF/manifest.xml")
        archive = {info.filename: zin.read(info.filename) for info in zin.infolist()}

    root = ET.fromstring(content)
    text_el = root.find(".//office:text", NS)
    if text_el is None:
        raise RuntimeError("office:text não encontrado")

    children = list(text_el)
    sec3_start = find_paragraph_index(
        text_el, lambda t: t.strip().startswith("3.") and "SEDA" in t.upper()
    )
    sec4_start = find_paragraph_index(
        text_el, lambda t: t.strip().startswith("4.") and "INTERFACE" in t.upper()
    )

    subsection_tpl = None
    for node in children[sec3_start:sec4_start]:
        if node.tag == qname("text", "p") and re.match(r"3\.\d", para_text(node)):
            subsection_tpl = node
            break
    if subsection_tpl is None:
        subsection_tpl = children[sec3_start + 15]

    templates = {
        "chapter": children[sec3_start],
        "subsection": subsection_tpl,
        "table2": children[123],
        "table3": children[262],
        "image_p": children[5],
    }

    new_block = build_section_3(templates) + build_architecture_chapter(templates)

    for node in list(text_el)[sec3_start:sec4_start]:
        text_el.remove(node)

    for offset, node in enumerate(new_block):
        text_el.insert(sec3_start + offset, node)

    # Renumerar Interface gráfica 4 → 5
    for child in text_el.findall("text:p", NS):
        t = para_text(child)
        if re.match(r"4\.\)\s*Interface", t, re.I):
            for sub in list(child):
                child.remove(sub)
            child.text = "5.) Interface gráfica"
            break

    # Índice (Tabela9)
    for child in list(text_el):
        if child.tag == qname("table", "table") and child.get(qname("table", "name")) == "Tabela9":
            update_index_table(child)
            break

    new_content = ET.tostring(root, encoding="utf-8", xml_declaration=True)
    new_manifest = add_manifest_entry(manifest, ARCH_IMAGE_ODT)
    archive["content.xml"] = new_content
    archive["META-INF/manifest.xml"] = new_manifest
    archive[ARCH_IMAGE_ODT] = ARCH_IMAGE_SRC.read_bytes()

    temp_odt = ODT_PATH.with_suffix(".tmp.odt")
    with zipfile.ZipFile(temp_odt, "w", compression=zipfile.ZIP_DEFLATED) as zout:
        for name, data in archive.items():
            zout.writestr(name, data)

    temp_odt.replace(ODT_PATH)
    print(f"Atualizado: {ODT_PATH}")
    print(f"Backup: {BACKUP_PATH}")
    print(f"Seção 3: Projeto ProjMap ({len(SECTION3_PARAGRAPHS)} parágrafos)")
    print("Capítulo 4: Arquitetura inserido")
    print(f"Imagem: {ARCH_IMAGE_ODT}")


if __name__ == "__main__":
    main()

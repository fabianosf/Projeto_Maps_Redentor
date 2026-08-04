# -*- coding: utf-8 -*-
"""
Insere o diagrama completo de pastas do repositório na seção
'9.2 Estrutura de pastas do projeto' do Doc_Proj_Map.odt.
"""

from __future__ import annotations

import copy
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from odt_lib import NS, ODT_PATH, read_content_root, write_content_xml

SECTION_TITLE = "9.2 Estrutura de pastas do projeto"
NEXT_SECTION = "9.3 Comunicação entre componentes"
TREE_STYLE = "P52"  # mesmo estilo dos diagramas ASCII da arquitetura

FOLDER_TREE = [
    "PROJ_MAP/",
    "├── DAL/                              # Camada de acesso a dados (padrão PROJ_PAD)",
    "│   ├── PROJ_GAC/                     # Utilitário legado de configs criptografadas",
    "│   │   ├── geradorArquivoConfiguracao.py",
    "│   │   └── main.py",
    "│   ├── arquivos_crip/                # Configurações sensíveis (Fernet)",
    "│   │   ├── arq/                      # Arquivos .dat criptografados",
    "│   │   │   ├── map_MariaDB.dat       # Conexão MariaDB (banco map)",
    "│   │   │   ├── map_PostGree.dat      # Conexão PostgreSQL (opcional)",
    "│   │   │   └── …                     # Outros .dat de referência/legado",
    "│   │   └── chave/",
    "│   │       └── chave.key             # Chave Fernet (não versionar)",
    "│   ├── CONFIGURACAO.py               # Leitura/descriptografia dos .dat",
    "│   ├── DAL.py                        # Pool, queries, conexão DB",
    "│   └── __init__.py",
    "│",
    "├── Doc/                              # Documentação única do projeto",
    "│   └── Doc_Proj_Map.odt              # Especificação oficial",
    "│",
    "├── LOG/                              # Logging da aplicação",
    "│   ├── log/",
    "│   │   └── proj_map_log_*.log",
    "│   ├── LOG.py",
    "│   └── __init__.py",
    "│",
    "├── database/                         # Scripts SQL (DDL, seeds, migrações)",
    "│   ├── schema.sql                    # tb_perfil, tb_usuario + seeds",
    "│   ├── schema_operacional.sql        # tb_map, tb_item_map, tb_viagem, mestres",
    "│   ├── schema_seed.sql",
    "│   ├── schema_postgresql.sql",
    "│   └── schema_migrate_*.sql          # Migrações incrementais",
    "│",
    "├── FrontEnd/                         # FrontEnd — React Native (Expo)",
    "│   ├── App.tsx                       # App inicial",
    "│   ├── index.js",
    "│   ├── package.json",
    "│   ├── app.json",
    "│   ├── babel.config.js",
    "│   ├── tsconfig.json",
    "│   └── src/",
    "│       ├── api/                      # Chamadas HTTP à API Flask",
    "│       │   ├── client.ts",
    "│       │   └── auth.ts",
    "│       ├── config/                   # URL da API, perfis, senha 12345",
    "│       │   ├── api.ts",
    "│       │   └── constants.ts",
    "│       ├── navigation/               # Navegação (a implementar)",
    "│       ├── screens/                  # Telas RF-UI / RF-MAP-UI (a implementar)",
    "│       ├── types/",
    "│       │   └── index.ts",
    "│       └── utils/",
    "│           └── validation.ts         # RF-RN-007",
    "│",
    "├── BackEnd/                          # BackEnd — Flask (API REST)",
    "│   ├── app.py                        # Entry point (/api/v1)",
    "│   ├── auth_routes.py                # /api/v1/auth/*",
    "│   ├── auth_service.py               # Login, troca de senha, bcrypt",
    "│   ├── auth_session.py               # Cookie redmapa_sid",
    "│   ├── auth_middleware.py            # Sessão, Admin, acesso MAPA",
    "│   ├── session_store.py              # Sessão e change_token em memória",
    "│   ├── users_routes.py               # /api/v1/users/* (Admin)",
    "│   ├── users_service.py",
    "│   ├── mapa_routes.py                # /api/v1/mapa/*",
    "│   ├── mapa_service.py",
    "│   ├── constants.py                  # SENHA_PROVISORIA = 12345, perfis",
    "│   ├── DAL.py                        # Reexport → DAL/DAL.py",
    "│   ├── CONFIGURACAO.py               # Reexport → DAL/CONFIGURACAO.py",
    "│   └── __init__.py",
    "│",
    "├── scripts/                          # Automação (ODT, DB, scaffold)",
    "│   ├── odt_lib.py                    # Leitura/escrita Doc_Proj_Map.odt",
    "│   ├── scaffold_frontend.py          # Gera estrutura FrontEnd/",
    "│   ├── gerar_configs_map.py          # Gera .dat criptografados",
    "│   ├── setup_mariadb.ps1",
    "│   ├── reinstalar_mariadb.ps1",
    "│   ├── sync_odt_regras_negocio.py",
    "│   ├── sync_requisitos_odt.py",
    "│   └── update_odt_*.py               # Scripts de manutenção do ODT",
    "│",
    "├── .gitignore",
    "└── requirements.txt                  # Dependências Python (Flask, bcrypt, …)",
]

LAYERS_NOTE = [
    "Visão por camada:",
    "• FrontEnd → FrontEnd/ (React Native Expo)",
    "• BackEnd → BackEnd/ (API REST JSON /api/v1)",
    "• Dados → DAL/ + database/ (conexão DB + DDL/migrações)",
    "• Documentação → Doc/ (somente Doc_Proj_Map.odt)",
    "• Logs → LOG/",
    "• Ferramentas → scripts/",
]

FRONTEND_FIX_NEW = (
    "O FrontEnd React Native (Expo) está na pasta FrontEnd/ "
    "(App.tsx, src/api, src/config, src/navigation, src/screens, src/utils). "
    "A estrutura completa do repositório está na seção 9.2."
)


def para_text(el) -> str:
    return "".join(el.itertext()).strip().replace("\xa0", " ")


def make_para(style: str, text: str):
    from xml.etree.ElementTree import Element

    p = Element(f"{{{NS['text']}}}p")
    p.set(f"{{{NS['text']}}}style-name", style)
    p.text = text
    return p


def find_section_range(children: list, title: str, next_title: str) -> tuple[int, int]:
    start = end = None
    for i, c in enumerate(children):
        if not c.tag.endswith("p"):
            continue
        t = para_text(c)
        if t == title:
            start = i
        elif start is not None and t == next_title:
            end = i
            break
    if start is None or end is None:
        raise RuntimeError(f"Seção '{title}' → '{next_title}' não encontrada")
    return start, end


def main() -> None:
    root = read_content_root()
    text_el = root.find(".//office:text", NS)
    if text_el is None:
        raise RuntimeError("office:text não encontrado")

    # Corrigir parágrafo do FrontEnd (6.3.1)
    for p in text_el.findall("text:p", NS):
        t = para_text(p)
        if ("pasta mobile/" in t or "pasta FrontEnd/" in t) and (
            "src/api" in t or "pages/" in t or "assets/css" in t
        ):
            for ch in list(p):
                p.remove(ch)
            p.text = FRONTEND_FIX_NEW
            print("Corrigido parágrafo FrontEnd (6.3.1)")
            break

    children = list(text_el)
    start, end = find_section_range(children, SECTION_TITLE, NEXT_SECTION)

    # Remover conteúdo antigo entre o título e a próxima seção
    for idx in range(end - 1, start, -1):
        text_el.remove(children[idx])

    # Inserir árvore + nota de camadas após o título
    insert_at = start + 1
    nodes = [make_para("P51", "")]
    for line in FOLDER_TREE:
        nodes.append(make_para(TREE_STYLE, line))
    nodes.append(make_para("P51", ""))
    for line in LAYERS_NOTE:
        nodes.append(make_para(TREE_STYLE, line))
    nodes.append(make_para("P51", ""))

    for offset, node in enumerate(nodes):
        text_el.insert(insert_at + offset, node)

    write_content_xml(root)
    print(f"Atualizado: {ODT_PATH}")
    print(f"Linhas da árvore inseridas: {len(FOLDER_TREE)}")
    print(f"Seção: {SECTION_TITLE}")


if __name__ == "__main__":
    main()

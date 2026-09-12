# ----------------------------
# Deus seja Louvado!
# ----------------------------
"""
Seed local de motoristas fictícios para a tela “Vincular motorista”.

Identidade confiável: ``id_motorista`` (PK imutável).
- Vínculos de escala/item/guia devem continuar referenciando ``id_motorista``.
- ``matricula`` é atributo sincronizável/atualizável (hoje: TESTE00N temporárias).
- Futuro: importar matrícula real da empresa e
  ``UPDATE tb_motorista SET matricula = ? WHERE id_motorista = ?``
  sem recriar linhas — vínculos, histórico e auditoria permanecem intactos.

Uso (PostgreSQL local com BackEnd/.env):
  .venv/bin/python scripts/seed_motoristas_teste_vincular.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# (matricula_temporaria, nome_ficticio)
MOTORISTAS_TESTE = [
    ("TESTE001", "motorista_01"),
    ("TESTE002", "motorista_02"),
    ("TESTE003", "motorista_03"),
    ("TESTE004", "motorista_04"),
    ("TESTE005", "motorista_05"),
]


def _assegurar_motorista(dal, matricula: str, nome: str) -> str:
    """Insere ou reativa pelo match de matrícula; nunca altera id_motorista existente."""
    existente = dal.read(
        """
        SELECT id_motorista, nome, ativo
        FROM tb_motorista
        WHERE matricula = ?
        LIMIT 1
        """,
        (matricula,),
    )
    if existente is not None and not existente.empty:
        id_mot = int(existente.iloc[0]["id_motorista"])
        dal.update(
            """
            UPDATE tb_motorista
            SET nome = ?, ativo = 1
            WHERE id_motorista = ?
            """,
            (nome, id_mot),
        )
        return f"UPDATE id={id_mot} matricula={matricula} nome={nome}"

    ok = dal.create(
        """
        INSERT INTO tb_motorista (matricula, nome, ativo)
        VALUES (?, ?, 1)
        """,
        (matricula, nome),
    )
    if not ok:
        raise RuntimeError(f"Falha ao inserir motorista {matricula}")
    criado = dal.read(
        "SELECT id_motorista FROM tb_motorista WHERE matricula = ? LIMIT 1",
        (matricula,),
    )
    id_mot = int(criado.iloc[0]["id_motorista"]) if criado is not None and not criado.empty else "?"
    return f"INSERT id={id_mot} matricula={matricula} nome={nome}"


def main() -> int:
    from BackEnd.dal_factory import create_dal

    dal = create_dal()
    print(f"Seed motoristas teste vincular [sgbd={dal.get_sgbd()}]...")
    for matricula, nome in MOTORISTAS_TESTE:
        print(" ", _assegurar_motorista(dal, matricula, nome))

    mats = tuple(m[0] for m in MOTORISTAS_TESTE)
    placeholders = ", ".join("?" for _ in mats)
    conf = dal.read(
        f"""
        SELECT id_motorista, matricula, nome, ativo
        FROM tb_motorista
        WHERE matricula IN ({placeholders})
        ORDER BY matricula
        """,
        mats,
    )
    print("Confirmados:")
    if conf is None or conf.empty:
        print("  (nenhum)")
        return 1
    for _, row in conf.iterrows():
        print(
            f"  id_motorista={int(row['id_motorista'])} "
            f"matricula={row['matricula']} nome={row['nome']} ativo={row['ativo']}"
        )
    print("OK — vínculos futuros devem usar id_motorista; matricula é atualizável.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Garante tb_empresa com Futuro / Redentor / Barra (ordem do Select Tela 05)."""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dal_util import ScriptDal, create_dal

EMPRESAS = [(1, "Futuro"), (2, "Redentor"), (3, "Barra")]


def main() -> None:
    dal = create_dal()
    cur = ScriptDal(dal)

    cur.execute(
        "SELECT id_empresa, codigo_empresa, descricao, ativo FROM tb_empresa "
        "ORDER BY codigo_empresa, id_empresa"
    )
    print("antes:", cur.fetchall())

    for codigo, nome in EMPRESAS:
        cur.execute(
            "SELECT id_empresa FROM tb_empresa WHERE codigo_empresa=%s",
            (codigo,),
        )
        row = cur.fetchone()
        if row:
            cur.execute(
                "UPDATE tb_empresa SET descricao=%s, ativo=1 WHERE codigo_empresa=%s",
                (nome, codigo),
            )
        else:
            cur.execute(
                "INSERT INTO tb_empresa (codigo_empresa, descricao, ativo) VALUES (%s, %s, 1)",
                (codigo, nome),
            )

    cur.execute(
        "SELECT id_empresa, codigo_empresa, descricao, ativo FROM tb_empresa "
        "ORDER BY codigo_empresa, id_empresa"
    )
    print("depois:", cur.fetchall())


if __name__ == "__main__":
    main()

"""Adiciona coluna placa (HH:MM) em tb_viagem, se ainda nao existir."""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dal_util import ScriptDal, column_exists, create_dal

def main() -> None:
    dal = create_dal()
    cur = ScriptDal(dal)

    if column_exists(dal, "tb_viagem", "placa"):
        print("COLUNA placa JA EXISTE")
    else:
        dal.update(
            """
            ALTER TABLE tb_viagem
            ADD COLUMN placa VARCHAR(5) NULL
                COMMENT 'Horario auxiliar no formato HH:MM (campo Placa da UI)'
                AFTER horario_chegada
            """
        )
        print("COLUNA placa ADICIONADA")

    cur.execute("DESCRIBE tb_viagem")
    print(cur.fetchall())


if __name__ == "__main__":
    main()

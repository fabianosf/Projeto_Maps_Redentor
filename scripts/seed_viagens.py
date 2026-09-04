"""Insere viagens de teste para captura de telas."""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from dal_util import ScriptDal, create_dal

dal = create_dal()
cur = ScriptDal(dal)

cur.execute("SELECT placa FROM tb_veiculo WHERE id_veiculo=11")
row = cur.fetchone()
placa = row["placa"] if row else "ABC-1234"
print(f"Placa: {placa}")

viagens = [
    (1, "2026-08-05 05:10:00", "KK816", "2026-08-05 05:25:00", 15, 32, 28),
    (1, "2026-08-05 05:40:00", "KK816", "2026-08-05 05:55:00", 15, 28, 30),
    (1, "2026-08-05 06:10:00", "KK816", "2026-08-05 06:25:00", 15, 35, 25),
]
for v in viagens:
    cur.execute(
        "INSERT INTO tb_viagem (id_item_registro, horario_chegada, placa, horario_saida, intervalo, qtd_pas_ida, qtd_pas_volta) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s)",
        v,
    )
print(f"Inseridas {len(viagens)} viagens")

cur.execute("SELECT id_viagem, id_item_registro, placa, horario_chegada FROM tb_viagem")
print("tb_viagem:", cur.fetchall())

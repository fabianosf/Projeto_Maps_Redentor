# ----------------------------
# Deus seja Louvado!
# ----------------------------
"""Smoke: cria mapa real e verifica codigo_mapa (Red/Fut/Bar)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> int:
    from BackEnd.dal_factory import create_dal
    from BackEnd.mapa_service import MapaError, criar_mapa, excluir_mapa

    dal = create_dal()
    user = dal.read("SELECT id_usuario FROM tb_usuario WHERE ativo = 1 ORDER BY id_usuario LIMIT 1")
    if user is None or user.empty:
        print("Nenhum usuario ativo", file=sys.stderr)
        return 1
    id_usuario = int(user.iloc[0]["id_usuario"])
    turno = dal.read("SELECT id_turno FROM tb_turno WHERE ativo = 1 ORDER BY id_turno LIMIT 1")
    if turno is None or turno.empty:
        print("Nenhum turno ativo", file=sys.stderr)
        return 1
    id_turno = int(turno.iloc[0]["id_turno"])

    emp = dal.read(
        "SELECT id_empresa, descricao, prefixo_mapa FROM tb_empresa WHERE ativo = 1 ORDER BY id_empresa"
    )
    print("empresas", emp.to_dict(orient="records"))
    print("usuario", id_usuario, "turno", id_turno)

    ids = []
    for _, row in emp.iterrows():
        id_emp = int(row["id_empresa"])
        prefixo = str(row["prefixo_mapa"]).strip()
        res = criar_mapa(
            dal,
            id_usuario,
            {
                "id_turno": id_turno,
                "id_empresa": id_emp,
                "data": "2026-09-10",
                "inicio_jornada_des": "2026-09-10 05:00:00",
                "fim_jornada_des": "2026-09-10 14:00:00",
            },
        )
        if isinstance(res, MapaError):
            print("FALHA", id_emp, res.codigo, res.mensagem)
            return 1
        codigo = res.get("codigo_mapa")
        print(f"OK empresa={id_emp} ({row['descricao']}) -> {codigo} (cod_map interno={res.get('cod_map')})")
        if not str(codigo or "").startswith(prefixo):
            print("PREFIXO ERRADO", codigo, prefixo)
            return 1
        ids.append(int(res["id_registro"]))

    for id_reg in ids:
        excluir_mapa(dal, id_reg)
    print("smoke OK (mapas de teste removidos)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

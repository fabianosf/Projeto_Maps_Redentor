# ----------------------------
# Deus seja Louvado!
# ----------------------------

"""Cadastros mestres compartilhados (empresa, linha, turno, local, veículo, motorista)."""

from __future__ import annotations

from typing import Any


def _rows(dal, sql: str) -> list[dict[str, Any]]:
    df = dal.read(sql)
    if df.empty:
        return []
    records = df.to_dict(orient="records")
    out: list[dict[str, Any]] = []
    for row in records:
        clean: dict[str, Any] = {}
        for key, value in row.items():
            if value is None:
                clean[key] = None
            elif hasattr(value, "item"):
                try:
                    clean[key] = value.item()
                except Exception:
                    clean[key] = value
            else:
                clean[key] = value
        out.append(clean)
    return out


def listar_cadastros_mestres(dal) -> dict[str, list[dict[str, Any]]]:
    """Somente registros ativos — usado por Guia, Usuários, etc."""
    return {
        "empresas": _rows(dal, "SELECT * FROM tb_empresa WHERE ativo = 1 ORDER BY codigo_empresa"),
        "linhas": _rows(
            dal,
            """
            SELECT l.*, e.descricao AS empresa
            FROM tb_linha l
            INNER JOIN tb_empresa e ON e.id_empresa = l.id_empresa
            WHERE l.ativo = 1
            ORDER BY l.codigo_linha
            """,
        ),
        "turnos": _rows(dal, "SELECT * FROM tb_turno WHERE ativo = 1 ORDER BY codigo_turno"),
        "locais": _rows(dal, "SELECT * FROM tb_local WHERE ativo = 1 ORDER BY codigo_local"),
        "veiculos": _rows(
            dal,
            """
            SELECT id_veiculo, codigo_veiculo, numero_frota, placa, ativo
            FROM tb_veiculo
            WHERE ativo = 1
            ORDER BY CAST(numero_frota AS UNSIGNED), numero_frota
            """,
        ),
        "motoristas": _rows(
            dal,
            """
            SELECT id_motorista, matricula, nome, ativo
            FROM tb_motorista
            WHERE ativo = 1
            ORDER BY CAST(matricula AS UNSIGNED), matricula
            """,
        ),
    }

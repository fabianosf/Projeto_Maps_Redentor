# ----------------------------
# Deus seja Louvado!
# ----------------------------

"""Cadastro de vínculos indicador × perfil — tb_indicador / tb_ind_perf."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ServiceError:
    mensagem: str
    codigo: str = "erro_negocio"


def listar_indicadores_permitidos(dal, codigo_perfil: int) -> list[dict[str, Any]]:
    """RN-08 — indicadores vinculados ao perfil (somente leitura na Tela 04)."""
    df = dal.read(
        """
        SELECT i.id_ind, i.cod_ind, i.descricao, i.detalhe
        FROM tb_indicador i
        INNER JOIN tb_ind_perf ip ON ip.id_ind = i.id_ind
        INNER JOIN tb_perfil p ON p.id_perfil = ip.id_perfil
        WHERE p.codigo_perfil = ?
        ORDER BY i.cod_ind
        """,
        (codigo_perfil,),
    )
    if df.empty:
        return []
    return df.to_dict(orient="records")


def listar_indicadores(dal) -> list[dict[str, Any]]:
    """RF-52 — todos os indicadores cadastrados em tb_indicador."""
    df = dal.read(
        """
        SELECT id_ind, cod_ind, descricao, detalhe
        FROM tb_indicador
        ORDER BY cod_ind
        """
    )
    if df.empty:
        return []
    return df.to_dict(orient="records")


def listar_perfis(dal) -> list[dict[str, Any]]:
    df = dal.read(
        """
        SELECT id_perfil, codigo_perfil, descricao
        FROM tb_perfil
        ORDER BY codigo_perfil
        """
    )
    if df.empty:
        return []
    return df.to_dict(orient="records")


def _perfil_existe(dal, id_perfil: int) -> bool:
    df = dal.read(
        "SELECT id_perfil FROM tb_perfil WHERE id_perfil = ?",
        (id_perfil,),
    )
    return not df.empty


def listar_indicadores_com_vinculo(
    dal, id_perfil: int
) -> list[dict[str, Any]] | ServiceError:
    if not _perfil_existe(dal, id_perfil):
        return ServiceError("Perfil não encontrado.", "nao_encontrado")

    df = dal.read(
        """
        SELECT i.id_ind, i.cod_ind, i.descricao, i.detalhe,
               CASE WHEN ip.id_indperf IS NOT NULL THEN 1 ELSE 0 END AS vinculado
        FROM tb_indicador i
        LEFT JOIN tb_ind_perf ip
          ON ip.id_ind = i.id_ind AND ip.id_perfil = ?
        ORDER BY i.cod_ind
        """,
        (id_perfil,),
    )
    if df.empty:
        return []

    rows = df.to_dict(orient="records")
    for row in rows:
        row["vinculado"] = bool(int(row.get("vinculado") or 0))
    return rows


def salvar_vinculos_indicadores(
    dal,
    id_perfil: int,
    id_inds: list[int],
) -> bool | ServiceError:
    if not _perfil_existe(dal, id_perfil):
        return ServiceError("Perfil não encontrado.", "nao_encontrado")

    ids_validos: list[int] = []
    for raw in id_inds:
        try:
            iid = int(raw)
        except (TypeError, ValueError):
            continue
        if iid > 0:
            ids_validos.append(iid)

    if ids_validos:
        placeholders = ",".join("?" * len(ids_validos))
        df = dal.read(
            f"""
            SELECT id_ind FROM tb_indicador
            WHERE id_ind IN ({placeholders})
            """,
            tuple(ids_validos),
        )
        ids_validos = [int(r["id_ind"]) for r in df.to_dict(orient="records")]

    dal.delete("DELETE FROM tb_ind_perf WHERE id_perfil = ?", (id_perfil,))

    for id_ind in ids_validos:
        ok = dal.create(
            "INSERT INTO tb_ind_perf (id_ind, id_perfil) VALUES (?, ?)",
            (id_ind, id_perfil),
        )
        if not ok:
            return ServiceError("Não foi possível salvar os vínculos.", "persistencia")

    return True

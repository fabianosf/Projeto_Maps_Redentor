# ----------------------------
# Deus seja Louvado!
# ----------------------------

"""Contexto da tela Entrada | Saída — linhas e locais por vínculo do usuário."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional
from zoneinfo import ZoneInfo

_HHMM = re.compile(r"^\d{2}:\d{2}$")
_TZ_SP = ZoneInfo("America/Sao_Paulo")


@dataclass(frozen=True)
class EntradaSaidaError:
    mensagem: str
    codigo: str = "entrada_saida_error"


def _rows(dal, sql: str, params: tuple = ()) -> list[dict[str, Any]]:
    df = dal.read(sql, params)
    if df.empty:
        return []
    out: list[dict[str, Any]] = []
    for row in df.to_dict(orient="records"):
        item: dict[str, Any] = {}
        for k, v in row.items():
            if hasattr(v, "item"):
                try:
                    v = v.item()
                except Exception:
                    pass
            item[k] = v
        out.append(item)
    return out


def _obter_id_local_usuario(dal, id_usuario: int) -> Optional[int]:
    df = dal.read(
        "SELECT id_local FROM tb_usuario WHERE id_usuario = ?",
        (id_usuario,),
    )
    if df.empty:
        return None
    val = df.iloc[0]["id_local"]
    if val is None:
        return None
    try:
        n = int(val)
    except (TypeError, ValueError):
        return None
    return n if n > 0 else None


def _listar_linhas_por_local(dal, id_local: int) -> list[dict[str, Any]]:
    return _rows(
        dal,
        """
        SELECT l.id_linha, l.codigo_linha, l.descricao,
               l.id_local_origem, l.id_local_destino,
               lo.codigo_local AS codigo_origem, lo.descricao AS descricao_origem,
               ld.codigo_local AS codigo_destino, ld.descricao AS descricao_destino
        FROM tb_linha l
        INNER JOIN tb_local lo ON lo.id_local = l.id_local_origem
        INNER JOIN tb_local ld ON ld.id_local = l.id_local_destino
        WHERE l.ativo = 1
          AND (l.id_local_origem = ? OR l.id_local_destino = ?)
        ORDER BY l.codigo_linha
        """,
        (id_local, id_local),
    )


def obter_contexto_entrada_saida(
    dal, id_usuario: int
) -> dict[str, Any] | EntradaSaidaError:
    id_local = _obter_id_local_usuario(dal, id_usuario)
    locais = _rows(
        dal,
        """
        SELECT id_local, codigo_local, descricao
        FROM tb_local
        WHERE ativo = 1
        ORDER BY codigo_local
        """,
    )

    if id_local is None:
        return {
            "id_local_usuario": None,
            "local_usuario": None,
            "linhas": [],
            "locais": locais,
        }

    local_row = dal.read(
        """
        SELECT id_local, codigo_local, descricao
        FROM tb_local
        WHERE id_local = ? AND ativo = 1
        """,
        (id_local,),
    )
    local_usuario = None
    if not local_row.empty:
        local_usuario = local_row.iloc[0].to_dict()

    linhas = _listar_linhas_por_local(dal, id_local)
    return {
        "id_local_usuario": id_local,
        "local_usuario": local_usuario,
        "linhas": linhas,
        "locais": locais,
    }


def listar_linhas_saida_referencia(
    dal, id_usuario: int, id_linha_ref: int
) -> list[dict[str, Any]] | EntradaSaidaError:
    id_local = _obter_id_local_usuario(dal, id_usuario)
    if id_local is None:
        return []

    ref = dal.read(
        """
        SELECT id_linha, id_local_origem, id_local_destino
        FROM tb_linha
        WHERE id_linha = ? AND ativo = 1
        """,
        (id_linha_ref,),
    )
    if ref.empty:
        return EntradaSaidaError("Linha de referência inválida.", "linha_invalida")

    origem = int(ref.iloc[0]["id_local_origem"])
    destino = int(ref.iloc[0]["id_local_destino"])

    linhas = _rows(
        dal,
        """
        SELECT l.id_linha, l.codigo_linha, l.descricao,
               l.id_local_origem, l.id_local_destino,
               lo.codigo_local AS codigo_origem, lo.descricao AS descricao_origem,
               ld.codigo_local AS codigo_destino, ld.descricao AS descricao_destino
        FROM tb_linha l
        INNER JOIN tb_local lo ON lo.id_local = l.id_local_origem
        INNER JOIN tb_local ld ON ld.id_local = l.id_local_destino
        WHERE l.ativo = 1
          AND l.id_linha <> ?
          AND (l.id_local_origem = ? OR l.id_local_destino = ?)
          AND (l.id_local_origem = ? OR l.id_local_destino = ?)
        ORDER BY l.codigo_linha
        """,
        (id_linha_ref, id_local, id_local, destino, origem),
    )

    if linhas:
        return linhas

    return _rows(
        dal,
        """
        SELECT l.id_linha, l.codigo_linha, l.descricao,
               l.id_local_origem, l.id_local_destino,
               lo.codigo_local AS codigo_origem, lo.descricao AS descricao_origem,
               ld.codigo_local AS codigo_destino, ld.descricao AS descricao_destino
        FROM tb_linha l
        INNER JOIN tb_local lo ON lo.id_local = l.id_local_origem
        INNER JOIN tb_local ld ON ld.id_local = l.id_local_destino
        WHERE l.ativo = 1
          AND l.id_linha <> ?
          AND (l.id_local_origem = ? OR l.id_local_destino = ?)
        ORDER BY l.codigo_linha
        """,
        (id_linha_ref, id_local, id_local),
    )


def _id_veiculo_por_frota(dal, numero: str) -> Optional[int]:
    numero = (numero or "").strip()
    if not numero:
        return None
    df = dal.read(
        "SELECT id_veiculo FROM tb_veiculo WHERE ativo = 1 AND numero_frota = ? LIMIT 1",
        (numero,),
    )
    if df.empty:
        return None
    return int(df.iloc[0]["id_veiculo"])


def _validar_hhmm(valor: str) -> bool:
    valor = (valor or "").strip()
    if not _HHMM.match(valor):
        return False
    hh, mm = valor.split(":")
    return 0 <= int(hh) <= 23 and 0 <= int(mm) <= 59


def _id_guia_por_veiculo_data_atual_sem_largada(
    dal, id_veiculo: int
) -> Optional[int]:
    """
    RF-58 — id_guia em tb_guia com o mesmo carro, data atual e horário de
    largada (hor_fim) nulo/em branco.
    """
    if id_veiculo <= 0:
        return None
    hoje = datetime.now(_TZ_SP).date().isoformat()
    df = dal.read(
        """
        SELECT id_guia FROM tb_guia
        WHERE id_veiculo = ?
          AND DATE(data) = ?
          AND hor_fim IS NULL
        ORDER BY data DESC, id_guia DESC
        LIMIT 1
        """,
        (id_veiculo, hoje),
    )
    if df.empty:
        return None
    return int(df.iloc[0]["id_guia"])


def registrar_chegada_saida(
    dal,
    id_usuario: int,
    body: dict[str, Any],
) -> dict[str, Any] | EntradaSaidaError:
    evento = str(body.get("evento", "")).strip().upper()
    if evento not in ("C", "S"):
        return EntradaSaidaError("Evento inválido.", "validacao")

    try:
        id_linha = int(body.get("id_linha", 0))
    except (TypeError, ValueError):
        id_linha = 0
    if id_linha <= 0:
        return EntradaSaidaError("Selecione uma linha.", "validacao")

    ctx = obter_contexto_entrada_saida(dal, id_usuario)
    if isinstance(ctx, EntradaSaidaError):
        return ctx
    ids_linhas = {int(l["id_linha"]) for l in ctx.get("linhas", [])}
    if id_linha not in ids_linhas:
        return EntradaSaidaError("Linha não permitida para o usuário.", "linha_invalida")

    carro_txt = str(body.get("carro", "")).strip()
    id_veiculo = _id_veiculo_por_frota(dal, carro_txt)
    if id_veiculo is None:
        return EntradaSaidaError("Carro não encontrado.", "carro_invalido")

    id_guia = _id_guia_por_veiculo_data_atual_sem_largada(dal, id_veiculo)

    horario = str(body.get("horario", "")).strip()
    if not _validar_hhmm(horario):
        return EntradaSaidaError("Horário inválido.", "validacao")

    temp_raw = str(body.get("temperatura", "")).strip()
    temperatura = int(temp_raw) if temp_raw.isdigit() else None

    roleta = body.get("roleta")
    roleta_01 = int(roleta) if roleta not in (None, "") and str(roleta).isdigit() else None

    linha_destino = None
    destino = None
    if evento == "S":
        ld = body.get("linha_destino", body.get("id_linha_destino"))
        if ld not in (None, ""):
            try:
                linha_destino = int(ld)
            except (TypeError, ValueError):
                return EntradaSaidaError("Linha de saída inválida.", "validacao")
        dest_id = body.get("destino", body.get("id_destino"))
        if dest_id not in (None, ""):
            try:
                destino = int(dest_id)
            except (TypeError, ValueError):
                return EntradaSaidaError("Destino inválido.", "validacao")

    ok = dal.create(
        """
        INSERT INTO tb_chegada_saida (
            id_gui, id_linha, carro, evento, horario,
            roleta_01, roleta_02, temperatura, linha_destino, destino
        )
        VALUES (?, ?, ?, ?, ?, ?, NULL, ?, ?, ?)
        """,
        (
            id_guia,
            id_linha,
            id_veiculo,
            evento,
            horario,
            roleta_01,
            temperatura,
            linha_destino,
            destino,
        ),
    )
    if not ok:
        return EntradaSaidaError("Falha ao registrar chegada/saída.", "persistencia")
    return {"evento": evento, "id_linha": id_linha, "id_guia": id_guia}

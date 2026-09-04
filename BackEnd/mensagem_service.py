# ----------------------------
# Deus seja Louvado!
# ----------------------------

"""Tela Mensagem — tipos e registro de avaria (tb_tip_avaria, tb_avaria)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional


@dataclass(frozen=True)
class MensagemError:
    mensagem: str
    codigo: str = "mensagem_error"


def listar_tipos_avaria(dal) -> list[dict[str, Any]]:
    df = dal.read(
        """
        SELECT id_tip, descricao
        FROM tb_tip_avaria
        ORDER BY id_tip
        """
    )
    if df.empty:
        return []
    return df.to_dict(orient="records")


def _id_veiculo_por_frota(dal, numero_frota: str) -> Optional[int]:
    numero = (numero_frota or "").strip()
    if not numero:
        return None
    df = dal.read(
        """
        SELECT id_veiculo FROM tb_veiculo
        WHERE ativo = 1 AND numero_frota = ?
        LIMIT 1
        """,
        (numero,),
    )
    if df.empty:
        return None
    return int(df.iloc[0]["id_veiculo"])


def registrar_avaria(
    dal,
    id_usuario: int,
    numero_frota: str,
    id_tip: int,
    texto: str,
) -> dict[str, Any] | MensagemError:
    numero = (numero_frota or "").strip()
    texto_limpo = (texto or "").strip()
    if not numero or not numero.isdigit():
        return MensagemError("Informe o número do carro.", "validacao")
    if not id_tip:
        return MensagemError("Selecione o tipo de avaria.", "validacao")
    if not texto_limpo:
        return MensagemError("Informe o texto da mensagem.", "validacao")

    id_vei = _id_veiculo_por_frota(dal, numero)
    if id_vei is None:
        return MensagemError("Carro não encontrado.", "carro_invalido")

    tip = dal.read(
        "SELECT id_tip FROM tb_tip_avaria WHERE id_tip = ?",
        (id_tip,),
    )
    if tip.empty:
        return MensagemError("Tipo de avaria inválido.", "validacao")

    agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ok = dal.create(
        """
        INSERT INTO tb_avaria (id_vei, id_tip, id_usuario, data, texto)
        VALUES (?, ?, ?, ?, ?)
        """,
        (id_vei, id_tip, id_usuario, agora, texto_limpo),
    )
    if not ok:
        return MensagemError("Falha ao registrar a mensagem.", "persistencia")

    row = dal.read(
        """
        SELECT a.id_av, a.id_vei, a.id_tip, a.id_usuario, a.data, a.texto,
               t.descricao AS tipo_descricao, v.numero_frota
        FROM tb_avaria a
        INNER JOIN tb_tip_avaria t ON t.id_tip = a.id_tip
        INNER JOIN tb_veiculo v ON v.id_veiculo = a.id_vei
        ORDER BY a.id_av DESC
        LIMIT 1
        """
    )
    if row.empty:
        return {"ok": True}
    return row.iloc[0].to_dict()

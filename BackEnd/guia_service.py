# ----------------------------
# Deus seja Louvado!
# ----------------------------

"""Tela Guia — CRUD tb_guia."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional

_HHMM = re.compile(r"^\d{2}:\d{2}$")


@dataclass(frozen=True)
class GuiaError:
    mensagem: str
    codigo: str = "guia_error"


def _parse_int_opcional(valor: Any) -> Optional[int]:
    if valor is None or valor == "":
        return None
    try:
        n = int(valor)
    except (TypeError, ValueError):
        return None
    return n if n > 0 else None


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


def _id_motorista_por_matricula(dal, matricula: str) -> Optional[int]:
    matricula = (matricula or "").strip()
    if not matricula:
        return None
    df = dal.read(
        "SELECT id_motorista FROM tb_motorista WHERE ativo = 1 AND matricula = ? LIMIT 1",
        (matricula,),
    )
    if df.empty:
        return None
    return int(df.iloc[0]["id_motorista"])


def _data_br_para_sql(data_br: str) -> Optional[str]:
    data_br = (data_br or "").strip()
    m = re.match(r"^(\d{2})/(\d{2})/(\d{4})$", data_br)
    if not m:
        return None
    return f"{m.group(3)}-{m.group(2)}-{m.group(1)}"


def _datetime_guia(data_sql: Optional[str], hhmm: Optional[str]) -> Optional[str]:
    if not data_sql or not hhmm or not _HHMM.match(hhmm):
        return None
    return f"{data_sql} {hhmm}:00"


def _data_cadastro_agora() -> str:
    """Data/hora do cadastro persistida em tb_guia.data (DATETIME)."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _row_guia(dal, id_guia: int) -> Optional[dict[str, Any]]:
    df = dal.read(
        """
        SELECT g.*, v.numero_frota, m.matricula AS matricula_motorista
        FROM tb_guia g
        LEFT JOIN tb_veiculo v ON v.id_veiculo = g.id_veiculo
        LEFT JOIN tb_motorista m ON m.id_motorista = g.id_motorista
        WHERE g.id_guia = ?
        """,
        (id_guia,),
    )
    if df.empty:
        return None
    return df.iloc[0].to_dict()


def buscar_por_numero(dal, numero: str) -> dict[str, Any] | GuiaError:
    numero = (numero or "").strip()
    if not numero:
        return GuiaError("Informe o número da guia.", "validacao")
    df = dal.read(
        """
        SELECT g.*, v.numero_frota, m.matricula AS matricula_motorista
        FROM tb_guia g
        LEFT JOIN tb_veiculo v ON v.id_veiculo = g.id_veiculo
        LEFT JOIN tb_motorista m ON m.id_motorista = g.id_motorista
        WHERE g.numero = ?
        """,
        (numero,),
    )
    if df.empty:
        return GuiaError("Guia não encontrada.", "nao_encontrado")
    return df.iloc[0].to_dict()


def _validar_payload(body: dict[str, Any]) -> GuiaError | dict[str, Any]:
    numero = str(body.get("numero", "")).strip()
    if not numero:
        return GuiaError("NR(Guia) é obrigatório.", "validacao")
    if len(numero) > 15:
        return GuiaError("NR(Guia) deve ter no máximo 15 caracteres.", "validacao")

    data_sql = _data_br_para_sql(str(body.get("data", "")))
    if not data_sql:
        return GuiaError("Data inválida.", "validacao")

    hor_ini = str(body.get("hor_ini", body.get("horario_pegada", ""))).strip()
    hor_fim = str(body.get("hor_fim", body.get("horario_largada", ""))).strip()
    if hor_ini and not _HHMM.match(hor_ini):
        return GuiaError("INÍCIO(JORNADA) inválido.", "validacao")
    if hor_fim and not _HHMM.match(hor_fim):
        return GuiaError("FIM(JORNADA) inválido.", "validacao")

    obs = str(body.get("observacao", "")).strip()
    if len(obs) > 150:
        return GuiaError("Observação deve ter no máximo 150 caracteres.", "validacao")

    numero_frota = str(body.get("numero_frota", body.get("carro", ""))).strip()
    matricula_motorista = str(
        body.get("matricula_motorista", body.get("motorista", ""))
    ).strip()
    if numero_frota and (not numero_frota.isdigit() or len(numero_frota) > 5):
        return GuiaError("Carro deve conter até 5 dígitos numéricos.", "validacao")
    if matricula_motorista and (
        not matricula_motorista.isdigit() or len(matricula_motorista) > 5
    ):
        return GuiaError("Motorista deve conter até 5 dígitos numéricos.", "validacao")

    return {
        "numero": numero,
        "data_sql": data_sql,
        "id_empresa": _parse_int_opcional(body.get("id_empresa")),
        "id_linha": _parse_int_opcional(body.get("id_linha")),
        "id_turno": _parse_int_opcional(body.get("id_turno")),
        "id_veiculo": _parse_int_opcional(body.get("id_veiculo")),
        "id_motorista": _parse_int_opcional(body.get("id_motorista")),
        "numero_frota": numero_frota,
        "matricula_motorista": matricula_motorista,
        "hor_ini": hor_ini,
        "hor_fim": hor_fim,
        "roleta01_ini": _parse_int_opcional(
            body.get(
                "roleta01_ini",
                body.get(
                    "roleta01_inicial",
                    body.get("roleta_ini", body.get("roleta_inicial")),
                ),
            )
        ),
        "roleta01_fim": _parse_int_opcional(
            body.get(
                "roleta01_fim",
                body.get(
                    "roleta01_final",
                    body.get("roleta_fim", body.get("roleta_final")),
                ),
            )
        ),
        "roleta2_ini": _parse_int_opcional(
            body.get("roleta2_ini", body.get("roleta2_inicial"))
        ),
        "roleta2_fim": _parse_int_opcional(
            body.get("roleta2_fim", body.get("roleta2_final"))
        ),
        "observacao": obs or None,
    }


def _resolver_vinculos(dal, dados: dict[str, Any]) -> GuiaError | dict[str, Any]:
    id_veiculo = dados["id_veiculo"]
    if not id_veiculo and dados["numero_frota"]:
        id_veiculo = _id_veiculo_por_frota(dal, dados["numero_frota"])
        if id_veiculo is None:
            return GuiaError("Carro não encontrado.", "carro_invalido")

    id_motorista = dados["id_motorista"]
    if not id_motorista and dados["matricula_motorista"]:
        id_motorista = _id_motorista_por_matricula(dal, dados["matricula_motorista"])
        if id_motorista is None:
            return GuiaError("Motorista não encontrado.", "motorista_invalido")

    dados = {**dados, "id_veiculo": id_veiculo, "id_motorista": id_motorista}
    return dados


def criar_guia(dal, body: dict[str, Any]) -> dict[str, Any] | GuiaError:
    validado = _validar_payload(body)
    if isinstance(validado, GuiaError):
        return validado
    dados = _resolver_vinculos(dal, validado)
    if isinstance(dados, GuiaError):
        return dados

    existe = dal.read(
        "SELECT id_guia FROM tb_guia WHERE numero = ?",
        (dados["numero"],),
    )
    if not existe.empty:
        return GuiaError("NR(Guia) já cadastrado.", "numero_duplicado")

    ok = dal.create(
        """
        INSERT INTO tb_guia (
            numero, id_empresa, id_linha, id_turno, id_veiculo, id_motorista,
            hor_ini, hor_fim, roleta01_ini, roleta01_fim, roleta2_ini, roleta2_fim,
            observacao, data
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            dados["numero"],
            dados["id_empresa"],
            dados["id_linha"],
            dados["id_turno"],
            dados["id_veiculo"],
            dados["id_motorista"],
            _datetime_guia(dados["data_sql"], dados["hor_ini"]),
            _datetime_guia(dados["data_sql"], dados["hor_fim"]),
            dados["roleta01_ini"],
            dados["roleta01_fim"],
            dados["roleta2_ini"],
            dados["roleta2_fim"],
            dados["observacao"],
            _data_cadastro_agora(),
        ),
    )
    if not ok:
        return GuiaError("Falha ao salvar guia.", "persistencia")
    row = dal.read(
        "SELECT id_guia FROM tb_guia WHERE numero = ?",
        (dados["numero"],),
    )
    return _row_guia(dal, int(row.iloc[0]["id_guia"])) or {"ok": True}


def atualizar_guia(dal, id_guia: int, body: dict[str, Any]) -> dict[str, Any] | GuiaError:
    atual = dal.read("SELECT id_guia FROM tb_guia WHERE id_guia = ?", (id_guia,))
    if atual.empty:
        return GuiaError("Guia não encontrada.", "nao_encontrado")

    validado = _validar_payload(body)
    if isinstance(validado, GuiaError):
        return validado
    dados = _resolver_vinculos(dal, validado)
    if isinstance(dados, GuiaError):
        return dados

    dup = dal.read(
        "SELECT id_guia FROM tb_guia WHERE numero = ? AND id_guia <> ?",
        (dados["numero"], id_guia),
    )
    if not dup.empty:
        return GuiaError("NR(Guia) já cadastrado.", "numero_duplicado")

    ok = dal.update(
        """
        UPDATE tb_guia
        SET numero = ?, id_empresa = ?, id_linha = ?, id_turno = ?,
            id_veiculo = ?, id_motorista = ?, hor_ini = ?, hor_fim = ?,
            roleta01_ini = ?, roleta01_fim = ?, roleta2_ini = ?, roleta2_fim = ?,
            observacao = ?
        WHERE id_guia = ?
        """,
        (
            dados["numero"],
            dados["id_empresa"],
            dados["id_linha"],
            dados["id_turno"],
            dados["id_veiculo"],
            dados["id_motorista"],
            _datetime_guia(dados["data_sql"], dados["hor_ini"]),
            _datetime_guia(dados["data_sql"], dados["hor_fim"]),
            dados["roleta01_ini"],
            dados["roleta01_fim"],
            dados["roleta2_ini"],
            dados["roleta2_fim"],
            dados["observacao"],
            id_guia,
        ),
    )
    if not ok:
        return GuiaError("Falha ao atualizar guia.", "persistencia")
    row = _row_guia(dal, id_guia)
    if row is None:
        return GuiaError("Guia não encontrada.", "nao_encontrado")
    return row


def excluir_guia(dal, id_guia: int) -> GuiaError | None:
    em_uso = dal.read(
        "SELECT id_cs FROM tb_chegada_saida WHERE id_gui = ? LIMIT 1",
        (id_guia,),
    )
    if not em_uso.empty:
        return GuiaError("Guia vinculada a chegada/saída; não é possível excluir.", "guia_em_uso")
    ok = dal.delete("DELETE FROM tb_guia WHERE id_guia = ?", (id_guia,))
    if not ok:
        return GuiaError("Guia não encontrada.", "nao_encontrado")
    return None

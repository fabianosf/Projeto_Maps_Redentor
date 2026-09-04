# ----------------------------
# Deus seja Louvado!
# ----------------------------

"""Consulta de funcionários no ERP Oracle (Globus) — matrícula, nome e foto."""

from __future__ import annotations

import base64
import logging
from dataclasses import dataclass
from typing import Any, Optional

from .matricula_validation import matricula_valida

logger = logging.getLogger(__name__)

MSG_MATRICULA_INVALIDA = "Matrícula deve ser numérica com no máximo 5 dígitos."
MSG_ERP_NAO_ENCONTRADA = "Matrícula não encontrada no cadastro de funcionários."
MSG_ERP_INDISPONIVEL = (
    "Não foi possível consultar o cadastro de funcionários (ERP)."
)

_SQL_NOME = """
SELECT Globus.flp_funcionarios.NomeFunc AS NomeFunc
FROM Globus.flp_funcionarios
WHERE Globus.flp_funcionarios.CodFunc = ?
"""

_SQL_FOTO = """
SELECT Globus.flp_funcionarios.CodIntFunc AS CodIntFunc,
       Globus.flp_funcionarios.CodFunc AS CodFunc,
       Globus.flp_funcionarios_imagens.Imagem AS Imagem
FROM Globus.flp_funcionarios, Globus.flp_funcionarios_imagens
WHERE Globus.flp_funcionarios.CodIntFunc = Globus.flp_funcionarios_imagens.CodIntFunc
  AND Globus.flp_funcionarios.CodFunc = ?
"""


@dataclass(frozen=True)
class ErpError:
    mensagem: str
    codigo: str = "erp_erro"


def _param_matricula(matricula: str) -> int | str:
    """CodFunc no Oracle é numérico; usa int quando possível."""
    if matricula.isdigit():
        return int(matricula)
    return matricula


def _oracle_fetch_one(dal, sql: str, params: tuple) -> dict[str, Any] | None:
    """Executa SELECT retornando uma linha como dict (cursor nativo Oracle)."""
    conn = None
    cursor = None
    try:
        conn = dal.circuit_breaker.call(dal.pool.get_connection)
        cursor = conn.cursor()
        sql_adj, params_adj = dal._ajustar_sql_e_valores(sql, params)
        if params_adj is None:
            cursor.execute(sql_adj)
        else:
            cursor.execute(sql_adj, params_adj)
        row = cursor.fetchone()
        if row is None:
            return None
        cols = [col[0] for col in cursor.description]
        return dict(zip(cols, row))
    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None:
            dal.pool.return_connection(conn)


def _ler_blob(valor: Any) -> bytes | None:
    if valor is None:
        return None
    if isinstance(valor, (bytes, bytearray, memoryview)):
        return bytes(valor)
    if hasattr(valor, "read"):
        try:
            data = valor.read()
            return bytes(data) if data is not None else None
        except Exception:
            return None
    return None


def _detect_image_mime(data: bytes) -> str:
    if len(data) >= 2 and data[0:2] == b"\xff\xd8":
        return "image/jpeg"
    if len(data) >= 8 and data[0:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"
    if len(data) >= 6 and data[0:6] in (b"GIF87a", b"GIF89a"):
        return "image/gif"
    return "image/jpeg"


def _buscar_foto_erp(dal, matricula: str) -> tuple[Optional[str], Optional[str]]:
    """
    Busca foto no ERP. Falhas são silenciosas — retorna (None, None).
    """
    try:
        row = _oracle_fetch_one(dal, _SQL_FOTO, (_param_matricula(matricula),))
        if not row:
            return None, None
        blob = _ler_blob(row.get("IMAGEM") or row.get("Imagem"))
        if not blob:
            return None, None
        mime = _detect_image_mime(blob)
        return base64.b64encode(blob).decode("ascii"), mime
    except Exception as exc:
        logger.warning(
            "Falha ao obter foto ERP para matrícula %s: %s",
            matricula,
            exc,
            exc_info=True,
        )
        return None, None


def matricula_existe_erp(erp_dal, matricula: str) -> bool | ErpError:
    """Verifica se a matrícula existe no cadastro de funcionários Oracle."""
    matricula = (matricula or "").strip()
    if not matricula_valida(matricula):
        return ErpError(MSG_MATRICULA_INVALIDA, "validacao")

    try:
        row = _oracle_fetch_one(
            erp_dal, _SQL_NOME, (_param_matricula(matricula),)
        )
    except Exception as exc:
        logger.error(
            "Erro ao consultar matrícula %s no ERP: %s",
            matricula,
            exc,
            exc_info=True,
        )
        return ErpError(MSG_ERP_INDISPONIVEL, "erp_indisponivel")

    if not row:
        return ErpError(MSG_ERP_NAO_ENCONTRADA, "nao_encontrado_erp")

    nome = row.get("NomeFunc") or row.get("NOMEFUNC")
    if nome is None or str(nome).strip() == "":
        return ErpError(MSG_ERP_NAO_ENCONTRADA, "nao_encontrado_erp")

    return True


def consultar_funcionario_erp(erp_dal, matricula: str) -> dict[str, Any] | ErpError:
    """
    Retorna cod_func, nome e foto (base64) do ERP.
    Falha na foto não impede retorno de matrícula/nome.
    """
    matricula = (matricula or "").strip()
    if not matricula_valida(matricula):
        return ErpError(MSG_MATRICULA_INVALIDA, "validacao")

    try:
        row = _oracle_fetch_one(
            erp_dal, _SQL_NOME, (_param_matricula(matricula),)
        )
    except Exception as exc:
        logger.error(
            "Erro ao consultar funcionário %s no ERP: %s",
            matricula,
            exc,
            exc_info=True,
        )
        return ErpError(MSG_ERP_INDISPONIVEL, "erp_indisponivel")

    if not row:
        return ErpError(MSG_ERP_NAO_ENCONTRADA, "nao_encontrado_erp")

    nome_raw = row.get("NomeFunc") or row.get("NOMEFUNC")
    if nome_raw is None or str(nome_raw).strip() == "":
        return ErpError(MSG_ERP_NAO_ENCONTRADA, "nao_encontrado_erp")

    nome = str(nome_raw).strip()
    foto_base64, foto_mime = _buscar_foto_erp(erp_dal, matricula)

    resultado: dict[str, Any] = {
        "cod_func": matricula,
        "nome": nome,
        "foto_base64": foto_base64,
        "foto_mime": foto_mime,
    }
    return resultado


def anexar_foto_erp(erp_dal, matricula: str, destino: dict[str, Any]) -> dict[str, Any]:
    """
    Adiciona foto_base64/foto_mime ao dict destino.
    Erros na foto são ignorados — destino permanece inalterado em caso de falha.
    """
    foto_base64, foto_mime = _buscar_foto_erp(erp_dal, matricula)
    if foto_base64:
        destino["foto_base64"] = foto_base64
        destino["foto_mime"] = foto_mime
    else:
        destino["foto_base64"] = None
        destino["foto_mime"] = None
    return destino

# ----------------------------
# Deus seja Louvado!
# ----------------------------

"""DesignacaoOperacional — histórico de alocação do despachante (Fase 0/1)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Optional

from .constants import PERFIL_DESPACHANTE

STATUS_ATIVA = "ATIVA"
STATUS_ENCERRADA = "ENCERRADA"

_SELECT_DESIG = """
    SELECT
        d.id_designacao,
        d.id_usuario,
        d.id_empresa,
        e.descricao AS empresa,
        d.id_turno,
        t.descricao AS turno,
        d.id_linha,
        l.descricao AS linha,
        d.id_veiculo,
        v.numero_frota,
        d.data,
        d.inicio,
        d.fim,
        d.status,
        d.criado_em,
        d.encerrado_em,
        d.id_admin
    FROM tb_designacao_operacional d
    INNER JOIN tb_empresa e ON e.id_empresa = d.id_empresa
    INNER JOIN tb_turno t ON t.id_turno = d.id_turno
    LEFT JOIN tb_linha l ON l.id_linha = d.id_linha
    LEFT JOIN tb_veiculo v ON v.id_veiculo = d.id_veiculo
"""


@dataclass(frozen=True)
class ServiceError:
    mensagem: str
    codigo: str = "erro_negocio"


def _parse_id_opcional(valor: Any) -> Optional[int]:
    if valor is None or valor == "":
        return None
    try:
        n = int(valor)
    except (TypeError, ValueError):
        return None
    return n if n > 0 else None


def _parse_id_obrigatorio(valor: Any, rotulo: str) -> int | ServiceError:
    n = _parse_id_opcional(valor)
    if n is None:
        return ServiceError(f"{rotulo} é obrigatório.", "validacao")
    return n


def _row_to_dict(row) -> dict[str, Any]:
    def _raw(key: str):
        try:
            v = row[key]
        except Exception:
            return None
        if v is None:
            return None
        try:
            if v != v:  # NaN
                return None
        except Exception:
            pass
        return v

    def _iso(v):
        if v is None:
            return None
        if hasattr(v, "isoformat"):
            if isinstance(v, datetime):
                return v.isoformat(sep=" ")
            return v.isoformat()
        return str(v)

    id_linha = _raw("id_linha")
    id_veiculo = _raw("id_veiculo")
    id_admin = _raw("id_admin")
    return {
        "id_designacao": int(_raw("id_designacao")),
        "id_usuario": int(_raw("id_usuario")),
        "id_empresa": int(_raw("id_empresa")),
        "empresa": str(_raw("empresa")) if _raw("empresa") is not None else None,
        "id_turno": int(_raw("id_turno")),
        "turno": str(_raw("turno")) if _raw("turno") is not None else None,
        "id_linha": int(id_linha) if id_linha is not None else None,
        "linha": str(_raw("linha")) if _raw("linha") is not None else None,
        "id_veiculo": int(id_veiculo) if id_veiculo is not None else None,
        "numero_frota": (
            str(_raw("numero_frota")) if _raw("numero_frota") is not None else None
        ),
        "data": _iso(_raw("data")),
        "inicio": _iso(_raw("inicio")),
        "fim": _iso(_raw("fim")),
        "status": str(_raw("status")),
        "criado_em": _iso(_raw("criado_em")),
        "encerrado_em": _iso(_raw("encerrado_em")),
        "id_admin": int(id_admin) if id_admin is not None else None,
    }


def _parse_data(valor: Any) -> str | ServiceError:
    if valor is None or str(valor).strip() == "":
        return ServiceError("Data é obrigatória.", "validacao")
    s = str(valor).strip()[:10]
    try:
        date.fromisoformat(s)
    except ValueError:
        return ServiceError("Data inválida (use YYYY-MM-DD).", "validacao")
    return s


def _parse_inicio(valor: Any) -> str | ServiceError:
    if valor is None or str(valor).strip() == "":
        return ServiceError("Início é obrigatório.", "validacao")
    s = str(valor).strip().replace("T", " ")
    if len(s) == 16:
        s = f"{s}:00"
    try:
        datetime.strptime(s[:19], "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return ServiceError("Início inválido (use YYYY-MM-DD HH:MM[:SS]).", "validacao")
    return s[:19]


def _contar_ativas(dal, id_usuario: int) -> int:
    df = dal.read(
        """
        SELECT COUNT(*) AS qtd
        FROM tb_designacao_operacional
        WHERE id_usuario = ? AND status = ?
        """,
        (id_usuario, STATUS_ATIVA),
    )
    if df.empty:
        return 0
    return int(df.iloc[0]["qtd"])


def obter_ativa(dal, id_usuario: int) -> dict[str, Any] | None:
    df = dal.read(
        _SELECT_DESIG
        + """
        WHERE d.id_usuario = ? AND d.status = ?
        ORDER BY d.id_designacao DESC
        """,
        (int(id_usuario), STATUS_ATIVA),
    )
    if df.empty:
        return None
    return _row_to_dict(df.iloc[0])


def listar_historico(dal, id_usuario: int) -> list[dict[str, Any]]:
    df = dal.read(
        _SELECT_DESIG
        + """
        WHERE d.id_usuario = ?
        ORDER BY d.inicio DESC, d.id_designacao DESC
        """,
        (int(id_usuario),),
    )
    if df.empty:
        return []
    return [_row_to_dict(df.iloc[i]) for i in range(len(df))]


def _validar_despachante(dal, id_usuario: int) -> ServiceError | None:
    df = dal.read(
        """
        SELECT u.ativo, p.codigo_perfil
        FROM tb_usuario u
        INNER JOIN tb_perfil p ON p.id_perfil = u.id_perfil
        WHERE u.id_usuario = ?
        """,
        (id_usuario,),
    )
    if df.empty:
        return ServiceError("Usuário não encontrado.", "nao_encontrado")
    if int(df.iloc[0]["ativo"]) == 0:
        return ServiceError("Usuário inativo.", "usuario_inativo")
    if int(df.iloc[0]["codigo_perfil"]) != PERFIL_DESPACHANTE:
        return ServiceError(
            "Designação operacional aplica-se apenas a despachantes.",
            "perfil_invalido",
        )
    return None


def _validar_contexto(
    dal,
    *,
    id_empresa: int,
    id_turno: int,
    id_linha: Optional[int],
    id_veiculo: Optional[int],
) -> ServiceError | None:
    emp = dal.read(
        "SELECT id_empresa FROM tb_empresa WHERE id_empresa = ? AND ativo = 1",
        (id_empresa,),
    )
    if emp.empty:
        return ServiceError("Empresa inválida ou inativa.", "validacao")

    tur = dal.read(
        "SELECT id_turno FROM tb_turno WHERE id_turno = ? AND ativo = 1",
        (id_turno,),
    )
    if tur.empty:
        return ServiceError("Turno inválido ou inativo.", "validacao")

    if id_linha is not None:
        lin = dal.read(
            """
            SELECT id_linha, id_empresa FROM tb_linha
            WHERE id_linha = ? AND ativo = 1
            """,
            (id_linha,),
        )
        if lin.empty:
            return ServiceError("Linha inválida ou inativa.", "validacao")
        if int(lin.iloc[0]["id_empresa"]) != id_empresa:
            return ServiceError(
                "Linha não pertence à empresa da designação.",
                "validacao",
            )

    if id_veiculo is not None:
        vei = dal.read(
            """
            SELECT id_veiculo, id_empresa FROM tb_veiculo
            WHERE id_veiculo = ? AND ativo = 1
            """,
            (id_veiculo,),
        )
        if vei.empty:
            return ServiceError("Veículo inválido ou inativo.", "validacao")
        emp_v = vei.iloc[0].get("id_empresa")
        if emp_v is not None and str(emp_v) not in ("", "None", "nan"):
            if int(emp_v) != id_empresa:
                return ServiceError(
                    "Veículo não pertence à empresa da designação.",
                    "validacao",
                )
    return None


def _inserir_ativa(
    dal,
    *,
    id_usuario: int,
    id_empresa: int,
    id_turno: int,
    id_linha: Optional[int],
    id_veiculo: Optional[int],
    data_desig: str,
    inicio: str,
    id_admin: Optional[int],
) -> ServiceError | dict[str, Any]:
    ok = dal.create(
        """
        INSERT INTO tb_designacao_operacional (
            id_usuario, id_empresa, id_turno, id_linha, id_veiculo,
            data, inicio, fim, status, criado_em, encerrado_em, id_admin
        ) VALUES (?, ?, ?, ?, ?, ?, ?, NULL, ?, CURRENT_TIMESTAMP, NULL, ?)
        """,
        (
            id_usuario,
            id_empresa,
            id_turno,
            id_linha,
            id_veiculo,
            data_desig,
            inicio,
            STATUS_ATIVA,
            id_admin,
        ),
    )
    if not ok:
        return ServiceError("Falha ao gravar designação.", "persistencia")
    ativa = obter_ativa(dal, id_usuario)
    if ativa is None:
        return ServiceError("Falha ao recuperar designação criada.", "persistencia")
    return ativa


def criar_designacao(
    dal,
    *,
    id_usuario: Any,
    id_empresa: Any,
    id_turno: Any,
    data: Any,
    inicio: Any,
    id_linha: Any = None,
    id_veiculo: Any = None,
    id_admin: Optional[int] = None,
) -> ServiceError | dict[str, Any]:
    uid = _parse_id_obrigatorio(id_usuario, "Usuário")
    if isinstance(uid, ServiceError):
        return uid
    emp = _parse_id_obrigatorio(id_empresa, "Empresa")
    if isinstance(emp, ServiceError):
        return emp
    tur = _parse_id_obrigatorio(id_turno, "Turno")
    if isinstance(tur, ServiceError):
        return tur
    data_desig = _parse_data(data)
    if isinstance(data_desig, ServiceError):
        return data_desig
    ini = _parse_inicio(inicio)
    if isinstance(ini, ServiceError):
        return ini
    lin = _parse_id_opcional(id_linha)
    vei = _parse_id_opcional(id_veiculo)

    err = _validar_despachante(dal, uid)
    if err:
        return err
    err = _validar_contexto(
        dal, id_empresa=emp, id_turno=tur, id_linha=lin, id_veiculo=vei
    )
    if err:
        return err

    if _contar_ativas(dal, uid) > 0:
        return ServiceError(
            "Já existe designação ATIVA. Use transferência.",
            "conflito_ativa",
        )

    return _inserir_ativa(
        dal,
        id_usuario=uid,
        id_empresa=emp,
        id_turno=tur,
        id_linha=lin,
        id_veiculo=vei,
        data_desig=data_desig,
        inicio=ini,
        id_admin=id_admin,
    )


def transferir_designacao(
    dal,
    *,
    id_usuario: Any,
    id_empresa: Any,
    id_turno: Any,
    data: Any,
    inicio: Any,
    id_linha: Any = None,
    id_veiculo: Any = None,
    id_admin: Optional[int] = None,
    fim: Any = None,
) -> ServiceError | dict[str, Any]:
    """Encerra ATIVA (se houver) e cria nova ATIVA na mesma transação."""
    uid = _parse_id_obrigatorio(id_usuario, "Usuário")
    if isinstance(uid, ServiceError):
        return uid
    emp = _parse_id_obrigatorio(id_empresa, "Empresa")
    if isinstance(emp, ServiceError):
        return emp
    tur = _parse_id_obrigatorio(id_turno, "Turno")
    if isinstance(tur, ServiceError):
        return tur
    data_desig = _parse_data(data)
    if isinstance(data_desig, ServiceError):
        return data_desig
    ini = _parse_inicio(inicio)
    if isinstance(ini, ServiceError):
        return ini
    lin = _parse_id_opcional(id_linha)
    vei = _parse_id_opcional(id_veiculo)

    err = _validar_despachante(dal, uid)
    if err:
        return err
    err = _validar_contexto(
        dal, id_empresa=emp, id_turno=tur, id_linha=lin, id_veiculo=vei
    )
    if err:
        return err

    fim_txt = ini
    if fim is not None and str(fim).strip():
        fim_parsed = _parse_inicio(fim)
        if isinstance(fim_parsed, ServiceError):
            return fim_parsed
        fim_txt = fim_parsed

    try:
        with dal.transaction():
            ativa = obter_ativa(dal, uid)
            if ativa is not None:
                ok_upd = dal.update(
                    """
                    UPDATE tb_designacao_operacional
                    SET status = ?, fim = ?, encerrado_em = CURRENT_TIMESTAMP
                    WHERE id_designacao = ? AND status = ?
                    """,
                    (
                        STATUS_ENCERRADA,
                        fim_txt,
                        int(ativa["id_designacao"]),
                        STATUS_ATIVA,
                    ),
                )
                if not ok_upd:
                    raise RuntimeError("Falha ao encerrar designação ativa.")

            ok_ins = dal.create(
                """
                INSERT INTO tb_designacao_operacional (
                    id_usuario, id_empresa, id_turno, id_linha, id_veiculo,
                    data, inicio, fim, status, criado_em, encerrado_em, id_admin
                ) VALUES (?, ?, ?, ?, ?, ?, ?, NULL, ?, CURRENT_TIMESTAMP, NULL, ?)
                """,
                (
                    uid,
                    emp,
                    tur,
                    lin,
                    vei,
                    data_desig,
                    ini,
                    STATUS_ATIVA,
                    id_admin,
                ),
            )
            if not ok_ins:
                raise RuntimeError("Falha ao criar nova designação.")

            qtd = _contar_ativas(dal, uid)
            if qtd != 1:
                raise RuntimeError(
                    f"Inconsistência: esperado 1 ATIVA, encontrado {qtd}."
                )

            nova = obter_ativa(dal, uid)
            if nova is None:
                raise RuntimeError("Nova designação não encontrada após insert.")
            return nova
    except Exception as exc:
        return ServiceError(
            str(exc) or "Falha na transferência da designação.",
            "persistencia",
        )

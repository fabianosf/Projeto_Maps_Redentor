# ----------------------------
# Deus seja Louvado!
# ----------------------------
"""Guia como jornada: abertura, trechos, troca linha/carro, encerramento."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Optional

from .guia_service import (
    GuiaError,
    _data_br_para_sql,
    _data_cadastro_agora,
    _datetime_guia,
    _horario_valido,
    _id_motorista_por_matricula,
    _id_veiculo_por_frota,
    _row_guia,
)

_HHMM = re.compile(r"^\d{2}:\d{2}$")
STATUS_ABERTA = "ABERTA"
STATUS_ENCERRADA = "ENCERRADA"
TRECHO_PLANEJADO = "PLANEJADO"
TRECHO_EM_TRANSITO = "EM_TRANSITO"
TRECHO_CONCLUIDO = "CONCLUIDO"
TRECHO_CANCELADO = "CANCELADO"
MOT_LIVRE = "LIVRE"
MOT_DISPONIVEL = "DISPONIVEL"
MOT_EM_TRANSITO = "EM_TRANSITO"
CAMPOS_ALTERACAO = frozenset({"linha", "veiculo", "rota"})
SENTIDOS = frozenset({"IDA", "VOLTA"})
ENTIDADES_AUDITORIA = frozenset({"guia", "trecho", "roleta"})
MOTIVOS_ENCERRAMENTO = frozenset({"fim_jornada", "transferencia_empresa"})
STATUS_TRECHO_ATIVOS = frozenset({TRECHO_PLANEJADO, TRECHO_EM_TRANSITO, TRECHO_CONCLUIDO})


def _safe_val(v: Any) -> Any:
    if v is None:
        return None
    if hasattr(v, "item"):
        try:
            return v.item()
        except Exception:
            pass
    if hasattr(v, "isoformat"):
        try:
            return v.isoformat(sep=" ", timespec="seconds")
        except Exception:
            pass
    # NaN
    try:
        if v != v:
            return None
    except Exception:
        pass
    return v


def _safe_dict(row: dict[str, Any]) -> dict[str, Any]:
    return {k: _safe_val(v) for k, v in row.items()}


def _parse_id(valor: Any, *, allow_zero: bool = False) -> Optional[int]:
    if valor is None or valor == "":
        return None
    try:
        n = int(valor)
    except (TypeError, ValueError):
        return None
    if allow_zero:
        return n if n >= 0 else None
    return n if n > 0 else None


def _agora() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _status_guia(row: dict[str, Any]) -> str:
    st = str(row.get("status") or "").strip().upper()
    if st in (STATUS_ABERTA, STATUS_ENCERRADA):
        return st
    if row.get("hor_fim"):
        return STATUS_ENCERRADA
    return STATUS_ABERTA


def _status_trecho(row: dict[str, Any]) -> str:
    st = str(row.get("status") or "").strip().upper()
    if st in (
        TRECHO_PLANEJADO,
        TRECHO_EM_TRANSITO,
        TRECHO_CONCLUIDO,
        TRECHO_CANCELADO,
    ):
        return st
    if row.get("hor_fim"):
        return TRECHO_CONCLUIDO
    if row.get("hor_ini"):
        return TRECHO_EM_TRANSITO
    return TRECHO_PLANEJADO


def _parse_dt_completo(valor: Any) -> Optional[datetime]:
    if valor is None or valor == "":
        return None
    s = str(valor).strip().replace("T", " ")
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            return datetime.strptime(s[:19] if len(s) >= 19 else s, fmt)
        except ValueError:
            continue
    return None


def _validar_intervalo_horarios(
    hor_ini: Any, hor_fim: Any
) -> GuiaError | None:
    di = _parse_dt_completo(hor_ini)
    df = _parse_dt_completo(hor_fim)
    if di is not None and df is not None and df < di:
        return GuiaError(
            "Horário fim não pode ser anterior ao início.",
            "horario_invalido",
        )
    return None


def _versao(row: dict[str, Any]) -> int:
    try:
        return max(1, int(row.get("versao") or 1))
    except (TypeError, ValueError):
        return 1


def _checar_versao(row: dict[str, Any], body: dict[str, Any]) -> GuiaError | None:
    if "versao" not in body and body.get("versao_esperada") is None:
        return None
    esperado = body.get("versao", body.get("versao_esperada"))
    try:
        esp = int(esperado)
    except (TypeError, ValueError):
        return GuiaError("Versão inválida.", "validacao")
    if esp != _versao(row):
        return GuiaError(
            "Registro alterado por outro usuário. Recarregue e tente novamente.",
            "conflito_versao",
        )
    return None


def _registrar_auditoria(
    dal,
    *,
    entidade: str,
    id_entidade: int,
    id_guia: Optional[int],
    id_usuario: int,
    campo: str,
    valor_anterior: Any,
    valor_novo: Any,
    motivo: str,
) -> GuiaError | None:
    ent = (entidade or "").strip().lower()
    if ent not in ENTIDADES_AUDITORIA:
        return GuiaError("Entidade de auditoria inválida.", "validacao")
    mot = (motivo or "").strip()
    if len(mot) < 5:
        return GuiaError(
            "Informe o motivo da alteração (mín. 5 caracteres).",
            "motivo_obrigatorio",
        )
    ok = dal.create(
        """
        INSERT INTO tb_guia_auditoria (
            entidade, id_entidade, id_guia, id_usuario,
            campo, valor_anterior, valor_novo, motivo, registrado_em
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            ent,
            int(id_entidade),
            int(id_guia) if id_guia is not None else None,
            int(id_usuario),
            str(campo)[:60],
            None if valor_anterior is None else str(valor_anterior)[:255],
            None if valor_novo is None else str(valor_novo)[:255],
            mot[:255],
            _agora(),
        ),
    )
    if not ok:
        return GuiaError("Falha ao registrar auditoria.", "persistencia")
    return None


def _totais_roleta(ini: Any, fim: Any) -> Optional[int]:
    try:
        if ini is None or fim is None:
            return None
        a, b = int(ini), int(fim)
        return b - a
    except (TypeError, ValueError):
        return None


def _enriquecer_trecho(row: dict[str, Any]) -> dict[str, Any]:
    out = _safe_dict(row)
    out["status"] = _status_trecho(out)
    out["versao"] = _versao(out)
    out["total_jae"] = _totais_roleta(out.get("jae_ini"), out.get("jae_fim"))
    out["total_riocard"] = _totais_roleta(out.get("riocard_ini"), out.get("riocard_fim"))
    # Nunca somar Ja E + RioCard
    return out


def listar_auditorias(dal, id_guia: int) -> list[dict[str, Any]]:
    df = dal.read(
        """
        SELECT a.*, u.nome AS despachante, u.matricula AS matricula_despachante
        FROM tb_guia_auditoria a
        LEFT JOIN tb_usuario u ON u.id_usuario = a.id_usuario
        WHERE a.id_guia = ?
        ORDER BY a.registrado_em DESC, a.id_auditoria DESC
        """,
        (int(id_guia),),
    )
    if df is None or getattr(df, "empty", True):
        return []
    return df.to_dict(orient="records")


def disponibilidade_veiculo(
    dal,
    id_veiculo: Optional[int],
    *,
    excluir_id_trecho: Optional[int] = None,
) -> dict[str, Any]:
    """Carro EM_TRANSITO se houver trecho aberto em qualquer guia."""
    out: dict[str, Any] = {
        "disponibilidade": MOT_DISPONIVEL,
        "id_guia": None,
        "id_trecho_em_transito": None,
        "numero_guia": None,
    }
    if not id_veiculo:
        return out
    params: list[Any] = [int(id_veiculo), TRECHO_EM_TRANSITO, STATUS_ABERTA]
    sql = """
        SELECT t.id_trecho, t.id_guia, g.numero
        FROM tb_guia_trecho t
        INNER JOIN tb_guia g ON g.id_guia = t.id_guia
        WHERE t.id_veiculo = ?
          AND UPPER(TRIM(COALESCE(t.status, ''))) = ?
          AND UPPER(TRIM(COALESCE(g.status, 'ABERTA'))) = ?
          AND g.hor_fim IS NULL
    """
    if excluir_id_trecho is not None:
        sql += " AND t.id_trecho <> ?"
        params.append(int(excluir_id_trecho))
    sql += " ORDER BY t.id_trecho DESC LIMIT 1"
    df = dal.read(sql, tuple(params))
    if df is None or getattr(df, "empty", True):
        return out
    out["disponibilidade"] = MOT_EM_TRANSITO
    out["id_trecho_em_transito"] = int(df.iloc[0]["id_trecho"])
    out["id_guia"] = int(df.iloc[0]["id_guia"])
    out["numero_guia"] = str(df.iloc[0].get("numero") or "")
    return out


def disponibilidade_motorista(
    dal,
    id_motorista: Optional[int],
    *,
    data_sql: Optional[str] = None,
) -> dict[str, Any]:
    """
    LIVRE — sem guia aberta (pode abrir nova Guia).
    DISPONIVEL — guia aberta sem trecho EM_TRANSITO (só próximo trecho da mesma Guia).
    EM_TRANSITO — trecho em andamento (indisponível para nova rota/Guia).
    """
    out: dict[str, Any] = {
        "disponibilidade": MOT_LIVRE,
        "id_guia_aberta": None,
        "id_trecho_em_transito": None,
        "id_veiculo_em_transito": None,
        "id_empresa": None,
    }
    if not id_motorista:
        return out

    params: list[Any] = [int(id_motorista), STATUS_ABERTA]
    sql = """
        SELECT id_guia, id_empresa, numero
        FROM tb_guia
        WHERE id_motorista = ?
          AND UPPER(TRIM(COALESCE(status, 'ABERTA'))) = ?
          AND hor_fim IS NULL
    """
    if data_sql:
        sql += " AND DATE(COALESCE(hor_ini, data)) = ?"
        params.append(data_sql)
    sql += " ORDER BY id_guia DESC LIMIT 1"
    guia_df = dal.read(sql, tuple(params))
    if guia_df is None or getattr(guia_df, "empty", True):
        return out

    id_guia = int(guia_df.iloc[0]["id_guia"])
    out["id_guia_aberta"] = id_guia
    emp = guia_df.iloc[0].get("id_empresa")
    out["id_empresa"] = int(emp) if emp is not None and str(emp) != "nan" else None
    out["numero_guia"] = str(guia_df.iloc[0].get("numero") or "")

    em = dal.read(
        """
        SELECT id_trecho, id_veiculo FROM tb_guia_trecho
        WHERE id_guia = ?
          AND UPPER(TRIM(COALESCE(status, ''))) = ?
        ORDER BY seq DESC, id_trecho DESC LIMIT 1
        """,
        (id_guia, TRECHO_EM_TRANSITO),
    )
    if em is not None and not getattr(em, "empty", True):
        out["disponibilidade"] = MOT_EM_TRANSITO
        out["id_trecho_em_transito"] = int(em.iloc[0]["id_trecho"])
        vei = em.iloc[0].get("id_veiculo")
        out["id_veiculo_em_transito"] = int(vei) if vei is not None else None
        return out

    out["disponibilidade"] = MOT_DISPONIVEL
    return out


def listar_trechos(dal, id_guia: int) -> list[dict[str, Any]]:
    df = dal.read(
        """
        SELECT t.*,
               l.codigo_linha, l.descricao AS linha_descricao,
               v.numero_frota,
               o.descricao AS origem_descricao,
               d.descricao AS destino_descricao
        FROM tb_guia_trecho t
        LEFT JOIN tb_linha l ON l.id_linha = t.id_linha
        LEFT JOIN tb_veiculo v ON v.id_veiculo = t.id_veiculo
        LEFT JOIN tb_local o ON o.id_local = t.id_local_origem
        LEFT JOIN tb_local d ON d.id_local = t.id_local_destino
        WHERE t.id_guia = ?
        ORDER BY t.seq ASC, t.id_trecho ASC
        """,
        (int(id_guia),),
    )
    if df is None or getattr(df, "empty", True):
        return []
    return [_enriquecer_trecho(r) for r in df.to_dict(orient="records")]


def listar_alteracoes(dal, id_guia: int) -> list[dict[str, Any]]:
    df = dal.read(
        """
        SELECT a.*, u.nome AS despachante, u.matricula AS matricula_despachante
        FROM tb_guia_alteracao a
        LEFT JOIN tb_usuario u ON u.id_usuario = a.id_usuario
        WHERE a.id_guia = ?
        ORDER BY a.registrado_em DESC, a.id_alteracao DESC
        """,
        (int(id_guia),),
    )
    if df is None or getattr(df, "empty", True):
        return []
    return df.to_dict(orient="records")


def obter_guia_completa(dal, id_guia: int) -> dict[str, Any] | GuiaError:
    guia = _row_guia(dal, int(id_guia))
    if not guia:
        return GuiaError("Guia não encontrada.", "nao_encontrado")
    guia = _safe_dict(guia)
    guia["status"] = _status_guia(guia)
    guia["versao"] = _versao(guia)
    guia["trechos"] = listar_trechos(dal, int(id_guia))
    guia["alteracoes"] = [_safe_dict(a) for a in listar_alteracoes(dal, int(id_guia))]
    guia["auditorias"] = [_safe_dict(a) for a in listar_auditorias(dal, int(id_guia))]
    data_sql = None
    raw = guia.get("hor_ini") or guia.get("data")
    if raw is not None:
        s = str(raw)
        if len(s) >= 10 and s[4] == "-":
            data_sql = s[:10]
    guia["motorista_disponibilidade"] = disponibilidade_motorista(
        dal, _parse_id(guia.get("id_motorista")), data_sql=data_sql
    )
    guia["veiculo_disponibilidade"] = disponibilidade_veiculo(
        dal, _parse_id(guia.get("id_veiculo"))
    )
    return guia


def _guia_aberta_motorista(
    dal,
    id_motorista: int,
    data_sql: str,
    *,
    id_empresa: Optional[int] = None,
    excluir_id: Optional[int] = None,
) -> Optional[dict[str, Any]]:
    params: list[Any] = [int(id_motorista), data_sql, STATUS_ABERTA]
    sql = """
        SELECT id_guia, id_empresa, numero, status
        FROM tb_guia
        WHERE id_motorista = ?
          AND DATE(COALESCE(hor_ini, data)) = ?
          AND UPPER(TRIM(COALESCE(status, 'ABERTA'))) = ?
          AND hor_fim IS NULL
    """
    if id_empresa is not None:
        sql += " AND id_empresa = ?"
        params.append(int(id_empresa))
    if excluir_id is not None:
        sql += " AND id_guia <> ?"
        params.append(int(excluir_id))
    sql += " ORDER BY id_guia DESC LIMIT 1"
    df = dal.read(sql, tuple(params))
    if df is None or getattr(df, "empty", True):
        return None
    return df.iloc[0].to_dict()


def _proxima_seq_trecho(dal, id_guia: int) -> int:
    df = dal.read(
        "SELECT COALESCE(MAX(seq), 0) AS m FROM tb_guia_trecho WHERE id_guia = ?",
        (int(id_guia),),
    )
    try:
        return int(df.iloc[0]["m"]) + 1
    except Exception:
        return 1


def _locais_da_linha(dal, id_linha: Optional[int]) -> tuple[Optional[int], Optional[int]]:
    if id_linha is None:
        return None, None
    df = dal.read(
        """
        SELECT id_local_origem, id_local_destino
        FROM tb_linha WHERE id_linha = ? LIMIT 1
        """,
        (int(id_linha),),
    )
    if df is None or getattr(df, "empty", True):
        return None, None
    o = df.iloc[0].get("id_local_origem")
    d = df.iloc[0].get("id_local_destino")
    try:
        return (int(o) if o is not None else None, int(d) if d is not None else None)
    except (TypeError, ValueError):
        return None, None


def criar_trecho_inicial(
    dal,
    id_guia: int,
    *,
    id_linha: Optional[int],
    id_veiculo: Optional[int],
    data_sql: str,
    hor_ini: Optional[str],
    hor_fim: Optional[str],
    chegada_ponto: Optional[str],
    jae_ini: Optional[int] = None,
    jae_fim: Optional[int] = None,
    riocard_ini: Optional[int] = None,
    riocard_fim: Optional[int] = None,
    id_usuario: Optional[int] = None,
    sentido: str = "IDA",
) -> dict[str, Any] | GuiaError | None:
    """
    Legado: abertura da jornada NÃO cria trecho.
    Início/fim da jornada pertencem ao motorista e não geram Ida/Volta
    nem colocam recursos em trânsito. Mantido como no-op compatível.
    """
    del (
        dal,
        id_guia,
        id_linha,
        id_veiculo,
        data_sql,
        hor_ini,
        hor_fim,
        chegada_ponto,
        jae_ini,
        jae_fim,
        riocard_ini,
        riocard_fim,
        id_usuario,
        sentido,
    )
    return None


def criar_trecho(
    dal, id_guia: int, body: dict[str, Any], id_usuario: int
) -> dict[str, Any] | GuiaError:
    guia = _row_guia(dal, int(id_guia))
    if not guia:
        return GuiaError("Guia não encontrada.", "nao_encontrado")
    if _status_guia(guia) != STATUS_ABERTA:
        return GuiaError(
            "Guia encerrada. Não é possível adicionar trechos.",
            "guia_encerrada",
        )

    data_sql = None
    data_raw = guia.get("hor_ini") or guia.get("data")
    if data_raw is not None:
        s = str(data_raw)
        if len(s) >= 10 and s[4] == "-":
            data_sql = s[:10]
    if not data_sql:
        return GuiaError("Data da guia inválida.", "validacao")

    id_mot = _parse_id(guia.get("id_motorista"))
    disp = disponibilidade_motorista(dal, id_mot, data_sql=data_sql)
    if disp["disponibilidade"] == MOT_EM_TRANSITO:
        return GuiaError(
            "Motorista em trânsito. Conclua o trecho atual antes de iniciar outro.",
            "motorista_em_transito",
        )
    if (
        disp["disponibilidade"] == MOT_DISPONIVEL
        and disp.get("id_guia_aberta") is not None
        and int(disp["id_guia_aberta"]) != int(id_guia)
    ):
        return GuiaError(
            "Motorista disponível apenas para a guia aberta atual. "
            "Não é permitido abrir trecho em guia paralela.",
            "guia_paralela",
        )

    sentido = str(body.get("sentido") or "IDA").strip().upper()
    if sentido not in SENTIDOS:
        return GuiaError("Sentido inválido. Use IDA ou VOLTA.", "validacao")

    id_linha = _parse_id(body.get("id_linha"))
    id_veiculo = _parse_id(body.get("id_veiculo"))
    frota = str(body.get("numero_frota") or body.get("carro") or "").strip()
    if not id_veiculo and frota:
        id_veiculo = _id_veiculo_por_frota(dal, frota)
        if id_veiculo is None:
            return GuiaError("Carro não encontrado.", "carro_invalido")

    # Carro é cadastro independente — não amarra id_empresa do veículo à guia.
    if id_veiculo is not None:
        vei_ok = dal.read(
            "SELECT id_veiculo, ativo FROM tb_veiculo WHERE id_veiculo = ?",
            (int(id_veiculo),),
        )
        if vei_ok is None or vei_ok.empty:
            return GuiaError("Carro não encontrado.", "carro_invalido")
        if int(vei_ok.iloc[0].get("ativo") or 0) not in (1, True):
            return GuiaError("Carro está inativo.", "carro_invalido")

    if id_linha is not None and guia.get("id_empresa") is not None:
        lin = dal.read(
            "SELECT id_empresa FROM tb_linha WHERE id_linha = ?",
            (int(id_linha),),
        )
        if lin is not None and not lin.empty:
            id_emp_l = lin.iloc[0].get("id_empresa")
            if id_emp_l is not None and int(id_emp_l) != int(guia["id_empresa"]):
                return GuiaError(
                    "Linha de outra empresa. Encerre a guia e abra outra na empresa destino.",
                    "empresa_diferente",
                )

    # Troca de carro: não herdar leituras do carro anterior
    veiculo_anterior = None
    trechos_prev = [
        t
        for t in listar_trechos(dal, int(id_guia))
        if _status_trecho(t) != TRECHO_CANCELADO
    ]
    if trechos_prev:
        veiculo_anterior = _parse_id(trechos_prev[-1].get("id_veiculo"))
    trocou_carro = (
        id_veiculo is not None
        and veiculo_anterior is not None
        and int(id_veiculo) != int(veiculo_anterior)
    )

    origem = _parse_id(body.get("id_local_origem"))
    destino = _parse_id(body.get("id_local_destino"))
    if origem is None or destino is None:
        o2, d2 = _locais_da_linha(dal, id_linha)
        origem = origem if origem is not None else o2
        destino = destino if destino is not None else d2

    hor_ini = str(body.get("hor_ini") or "").strip()
    hor_fim = str(body.get("hor_fim") or "").strip()
    if hor_ini and not _horario_valido(hor_ini):
        return GuiaError("Início do trecho inválido.", "validacao")
    if hor_fim and not _horario_valido(hor_fim):
        return GuiaError("Fim do trecho inválido.", "validacao")

    jae_ini = _parse_id(body.get("jae_ini"), allow_zero=True)
    jae_fim = _parse_id(body.get("jae_fim"), allow_zero=True)
    rio_ini = _parse_id(body.get("riocard_ini"), allow_zero=True)
    rio_fim = _parse_id(body.get("riocard_fim"), allow_zero=True)

    if trocou_carro:
        # Exige novas leituras iniciais quando o carro mudou
        if body.get("iniciar") or hor_ini:
            if jae_ini is None and rio_ini is None and "jae_ini" not in body and "riocard_ini" not in body:
                return GuiaError(
                    "Troca de carro: informe novas leituras iniciais (Ja E e/ou RioCard).",
                    "leituras_obrigatorias",
                )

    quer_iniciar = bool(body.get("iniciar")) or bool(hor_ini)
    if quer_iniciar and not hor_ini:
        return GuiaError(
            "Informe a SAÍDA real do trecho para iniciar o trânsito.",
            "saida_obrigatoria",
        )
    if hor_fim and not hor_ini:
        return GuiaError(
            "Informe a SAÍDA real antes da CHEGADA.",
            "saida_obrigatoria",
        )

    # PLANEJADO (pendente) sem saída; EM_TRANSITO só com SAÍDA real;
    # CONCLUIDO só com SAÍDA + CHEGADA reais (nunca usa fim da jornada).
    if hor_ini and hor_fim:
        st = TRECHO_CONCLUIDO
    elif hor_ini:
        st = TRECHO_EM_TRANSITO
    else:
        st = TRECHO_PLANEJADO

    ini_dt = _datetime_guia(data_sql, hor_ini) if hor_ini else None
    fim_dt = _datetime_guia(data_sql, hor_fim) if hor_fim else None
    err_int = _validar_intervalo_horarios(ini_dt, fim_dt)
    if err_int:
        return err_int

    # Carro em trânsito só impede iniciar (não bloqueia trecho PENDENTE).
    if st == TRECHO_EM_TRANSITO and id_veiculo is not None:
        disp_v = disponibilidade_veiculo(dal, id_veiculo)
        if disp_v["disponibilidade"] == MOT_EM_TRANSITO:
            return GuiaError(
                f"Carro em trânsito (guia {disp_v.get('numero_guia')}). "
                "Conclua ou cancele o trecho antes de iniciar outro.",
                "carro_em_transito",
            )

    seq = _proxima_seq_trecho(dal, int(id_guia))
    ok = dal.create(
        """
        INSERT INTO tb_guia_trecho (
            id_guia, seq, id_linha, id_veiculo,
            id_local_origem, id_local_destino, sentido, status,
            hor_ini, hor_fim, jae_ini, jae_fim, riocard_ini, riocard_fim,
            id_usuario, criado_em, versao
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
        """,
        (
            int(id_guia),
            seq,
            id_linha,
            id_veiculo,
            origem,
            destino,
            sentido,
            st,
            ini_dt,
            fim_dt,
            jae_ini,
            jae_fim,
            rio_ini,
            rio_fim,
            int(id_usuario),
            _agora(),
        ),
    )
    if not ok:
        return GuiaError("Falha ao salvar trecho.", "persistencia")

    # Atualiza snapshot atual no cabeçalho (compat)
    if id_linha is not None or id_veiculo is not None:
        dal.update(
            """
            UPDATE tb_guia
            SET id_linha = COALESCE(?, id_linha),
                id_veiculo = COALESCE(?, id_veiculo),
                versao = COALESCE(versao, 1) + 1
            WHERE id_guia = ?
            """,
            (id_linha, id_veiculo, int(id_guia)),
        )

    trechos = listar_trechos(dal, int(id_guia))
    trecho = trechos[-1] if trechos else None
    if not trecho:
        return GuiaError("Trecho não encontrado.", "persistencia")
    if not trocou_carro and veiculo_anterior is not None:
        trecho["sugestao_mesmo_carro"] = True
    elif trocou_carro:
        trecho["exige_novas_leituras"] = True
    return trecho

def atualizar_trecho(
    dal, id_trecho: int, body: dict[str, Any], id_usuario: int
) -> dict[str, Any] | GuiaError:
    df = dal.read(
        "SELECT * FROM tb_guia_trecho WHERE id_trecho = ?",
        (int(id_trecho),),
    )
    if df is None or getattr(df, "empty", True):
        return GuiaError("Trecho não encontrado.", "nao_encontrado")
    trecho = df.iloc[0].to_dict()
    id_guia = int(trecho["id_guia"])
    guia = _row_guia(dal, id_guia)
    if not guia:
        return GuiaError("Guia não encontrada.", "nao_encontrado")
    if _status_guia(guia) != STATUS_ABERTA:
        return GuiaError("Guia encerrada.", "guia_encerrada")

    err_v = _checar_versao(trecho, body)
    if err_v:
        return err_v

    data_sql = str(guia.get("hor_ini") or guia.get("data") or "")[:10]
    if len(data_sql) < 10:
        return GuiaError("Data da guia inválida.", "validacao")

    sentido = str(body.get("sentido") or trecho.get("sentido") or "IDA").strip().upper()
    if sentido not in SENTIDOS:
        return GuiaError("Sentido inválido.", "validacao")

    id_linha = _parse_id(body.get("id_linha"))
    if id_linha is None and "id_linha" not in body:
        id_linha = _parse_id(trecho.get("id_linha"))
    id_veiculo = _parse_id(body.get("id_veiculo"))
    if id_veiculo is None and "id_veiculo" not in body:
        frota = str(body.get("numero_frota") or body.get("carro") or "").strip()
        if frota:
            id_veiculo = _id_veiculo_por_frota(dal, frota)
        else:
            id_veiculo = _parse_id(trecho.get("id_veiculo"))

    origem = _parse_id(body.get("id_local_origem"))
    destino = _parse_id(body.get("id_local_destino"))
    if origem is None and destino is None:
        o2, d2 = _locais_da_linha(dal, id_linha)
        origem = _parse_id(trecho.get("id_local_origem")) or o2
        destino = _parse_id(trecho.get("id_local_destino")) or d2

    hor_ini = str(body.get("hor_ini") or "").strip()
    hor_fim = str(body.get("hor_fim") or "").strip()
    if hor_ini and not _horario_valido(hor_ini):
        return GuiaError("Início do trecho inválido.", "validacao")
    if hor_fim and not _horario_valido(hor_fim):
        return GuiaError("Fim do trecho inválido.", "validacao")

    def _roleta(campo: str, atual: Any) -> Optional[int]:
        if campo in body:
            return _parse_id(body.get(campo), allow_zero=True)
        return _parse_id(atual, allow_zero=True)

    novos = {
        "id_linha": id_linha,
        "id_veiculo": id_veiculo,
        "sentido": sentido,
        "jae_ini": _roleta("jae_ini", trecho.get("jae_ini")),
        "jae_fim": _roleta("jae_fim", trecho.get("jae_fim")),
        "riocard_ini": _roleta("riocard_ini", trecho.get("riocard_ini")),
        "riocard_fim": _roleta("riocard_fim", trecho.get("riocard_fim")),
    }
    mudancas: list[tuple[str, Any, Any]] = []
    for campo, novo in novos.items():
        ant = trecho.get(campo)
        ant_s = None if ant is None else str(ant)
        novo_s = None if novo is None else str(novo)
        if ant_s != novo_s:
            mudancas.append((campo, ant, novo))

    if hor_ini:
        mudancas.append(("hor_ini", trecho.get("hor_ini"), hor_ini))
    if hor_fim:
        mudancas.append(("hor_fim", trecho.get("hor_fim"), hor_fim))

    # Edição livre em PENDENTE (PLANEJADO sem saída).
    # CONCLUIDO / EM_TRANSITO com dados salvos → exige motivo + auditoria.
    st_atual = _status_trecho(trecho)
    pendente_sem_saida = st_atual == TRECHO_PLANEJADO and not trecho.get("hor_ini")
    exige_auditoria = (not pendente_sem_saida) and bool(mudancas)
    if st_atual == TRECHO_CONCLUIDO and mudancas:
        exige_auditoria = True
    if exige_auditoria:
        motivo = str(body.get("motivo") or body.get("justificativa") or "").strip()
        if len(motivo) < 5:
            return GuiaError(
                "Informe o motivo ao corrigir trecho já iniciado/concluído (mín. 5 caracteres).",
                "motivo_obrigatorio",
            )
        for campo, ant, novo in mudancas:
            err_a = _registrar_auditoria(
                dal,
                entidade="trecho",
                id_entidade=int(id_trecho),
                id_guia=id_guia,
                id_usuario=int(id_usuario),
                campo=campo,
                valor_anterior=ant,
                valor_novo=novo,
                motivo=motivo,
            )
            if err_a:
                return err_a

    st = st_atual
    if hor_fim:
        if st_atual == TRECHO_PLANEJADO and not (hor_ini or trecho.get("hor_ini")):
            return GuiaError(
                "Informe a SAÍDA real antes da CHEGADA.",
                "saida_obrigatoria",
            )
        if st_atual == TRECHO_PLANEJADO and (hor_ini or trecho.get("hor_ini")):
            # Registro completo de viagem já encerrada
            st = TRECHO_CONCLUIDO
        elif st_atual == TRECHO_EM_TRANSITO:
            st = TRECHO_CONCLUIDO
        elif st_atual == TRECHO_CONCLUIDO:
            st = TRECHO_CONCLUIDO
    elif hor_ini and st_atual == TRECHO_PLANEJADO:
        st = TRECHO_EM_TRANSITO

    if st == TRECHO_EM_TRANSITO and id_veiculo is not None:
        disp_v = disponibilidade_veiculo(
            dal, id_veiculo, excluir_id_trecho=int(id_trecho)
        )
        if disp_v["disponibilidade"] == MOT_EM_TRANSITO:
            return GuiaError(
                f"Carro em trânsito (guia {disp_v.get('numero_guia')}). "
                "Conclua ou cancele o trecho antes.",
                "carro_em_transito",
            )

    ok = dal.update(
        """
        UPDATE tb_guia_trecho
        SET id_linha = ?, id_veiculo = ?,
            id_local_origem = ?, id_local_destino = ?, sentido = ?, status = ?,
            hor_ini = COALESCE(?, hor_ini),
            hor_fim = COALESCE(?, hor_fim),
            jae_ini = ?, jae_fim = ?, riocard_ini = ?, riocard_fim = ?,
            id_usuario = ?, atualizado_em = ?,
            versao = COALESCE(versao, 1) + 1
        WHERE id_trecho = ?
        """,
        (
            id_linha,
            id_veiculo,
            origem,
            destino,
            sentido,
            st,
            _datetime_guia(data_sql, hor_ini) if hor_ini else None,
            _datetime_guia(data_sql, hor_fim) if hor_fim else None,
            novos["jae_ini"],
            novos["jae_fim"],
            novos["riocard_ini"],
            novos["riocard_fim"],
            int(id_usuario),
            _agora(),
            int(id_trecho),
        ),
    )
    if not ok:
        return GuiaError("Falha ao atualizar trecho.", "persistencia")
    for t in listar_trechos(dal, id_guia):
        if int(t.get("id_trecho") or 0) == int(id_trecho):
            return t
    return GuiaError("Trecho não encontrado.", "nao_encontrado")


def iniciar_trecho(
    dal, id_trecho: int, body: dict[str, Any], id_usuario: int
) -> dict[str, Any] | GuiaError:
    """Marca trecho EM_TRANSITO — bloqueia motorista e carro."""
    df = dal.read(
        "SELECT * FROM tb_guia_trecho WHERE id_trecho = ?",
        (int(id_trecho),),
    )
    if df is None or getattr(df, "empty", True):
        return GuiaError("Trecho não encontrado.", "nao_encontrado")
    trecho = df.iloc[0].to_dict()
    err_v = _checar_versao(trecho, body)
    if err_v:
        return err_v

    id_guia = int(trecho["id_guia"])
    guia = _row_guia(dal, id_guia)
    if not guia:
        return GuiaError("Guia não encontrada.", "nao_encontrado")
    if _status_guia(guia) != STATUS_ABERTA:
        return GuiaError("Guia encerrada.", "guia_encerrada")

    st = _status_trecho(trecho)
    if st == TRECHO_CANCELADO:
        return GuiaError("Trecho cancelado.", "trecho_cancelado")
    if st == TRECHO_CONCLUIDO:
        return GuiaError("Trecho já concluído.", "trecho_concluido")
    if st == TRECHO_EM_TRANSITO:
        return _enriquecer_trecho(trecho)

    data_sql = str(guia.get("hor_ini") or guia.get("data") or "")[:10]
    id_mot = _parse_id(guia.get("id_motorista"))
    disp = disponibilidade_motorista(
        dal, id_mot, data_sql=data_sql if len(data_sql) >= 10 else None
    )
    if disp["disponibilidade"] == MOT_EM_TRANSITO and disp.get(
        "id_trecho_em_transito"
    ) != int(id_trecho):
        return GuiaError(
            "Motorista já possui trecho em trânsito. Conclua ou cancele antes.",
            "motorista_em_transito",
        )

    id_veiculo = _parse_id(trecho.get("id_veiculo")) or _parse_id(guia.get("id_veiculo"))
    if id_veiculo is not None:
        disp_v = disponibilidade_veiculo(
            dal, id_veiculo, excluir_id_trecho=int(id_trecho)
        )
        if disp_v["disponibilidade"] == MOT_EM_TRANSITO:
            return GuiaError(
                f"Carro em trânsito (guia {disp_v.get('numero_guia')}). "
                "Conclua ou cancele o trecho antes.",
                "carro_em_transito",
            )

    hor_ini = str(body.get("hor_ini") or "").strip()
    if not hor_ini:
        return GuiaError(
            "Informe a SAÍDA real do trecho para iniciar o trânsito.",
            "saida_obrigatoria",
        )
    if not _horario_valido(hor_ini):
        return GuiaError("SAÍDA do trecho inválida.", "validacao")
    ini_dt = _datetime_guia(data_sql, hor_ini)
    if ini_dt is None:
        return GuiaError("SAÍDA do trecho inválida.", "validacao")

    # Lock otimista: só inicia se ainda PLANEJADO; grava SAÍDA real (não COALESCE legado).
    versao_atual = _versao(trecho)
    ok = dal.update(
        """
        UPDATE tb_guia_trecho
        SET status = ?, hor_ini = ?,
            id_usuario = ?, atualizado_em = ?,
            versao = COALESCE(versao, 1) + 1
        WHERE id_trecho = ?
          AND UPPER(TRIM(COALESCE(status, 'PLANEJADO'))) = ?
          AND COALESCE(versao, 1) = ?
        """,
        (
            TRECHO_EM_TRANSITO,
            ini_dt,
            int(id_usuario),
            _agora(),
            int(id_trecho),
            TRECHO_PLANEJADO,
            versao_atual,
        ),
    )
    if not ok:
        return GuiaError(
            "Não foi possível iniciar o trecho (já iniciado ou alterado por outro usuário).",
            "conflito_versao",
        )

    err_a = _registrar_auditoria(
        dal,
        entidade="trecho",
        id_entidade=int(id_trecho),
        id_guia=id_guia,
        id_usuario=int(id_usuario),
        campo="status",
        valor_anterior=st,
        valor_novo=TRECHO_EM_TRANSITO,
        motivo=str(body.get("motivo") or "Início do trecho"),
    )
    if err_a:
        return err_a

    for t in listar_trechos(dal, id_guia):
        if int(t.get("id_trecho") or 0) == int(id_trecho):
            return t
    return GuiaError("Trecho não encontrado.", "nao_encontrado")


def concluir_trecho(
    dal, id_trecho: int, body: dict[str, Any], id_usuario: int
) -> dict[str, Any] | GuiaError:
    """Conclui trecho → libera motorista e carro (DISPONIVEL); Guia permanece ABERTA."""
    df = dal.read(
        "SELECT * FROM tb_guia_trecho WHERE id_trecho = ?",
        (int(id_trecho),),
    )
    if df is None or getattr(df, "empty", True):
        return GuiaError("Trecho não encontrado.", "nao_encontrado")
    trecho = df.iloc[0].to_dict()
    err_v = _checar_versao(trecho, body)
    if err_v:
        return err_v

    id_guia = int(trecho["id_guia"])
    guia = _row_guia(dal, id_guia)
    if not guia:
        return GuiaError("Guia não encontrada.", "nao_encontrado")
    if _status_guia(guia) != STATUS_ABERTA:
        return GuiaError("Guia encerrada.", "guia_encerrada")

    st = _status_trecho(trecho)
    if st == TRECHO_CANCELADO:
        return GuiaError("Trecho cancelado.", "trecho_cancelado")
    if st == TRECHO_CONCLUIDO:
        return _enriquecer_trecho(trecho)
    if st == TRECHO_PLANEJADO:
        return GuiaError("Inicie o trecho antes de concluir.", "trecho_nao_iniciado")

    data_sql = str(guia.get("hor_ini") or guia.get("data") or "")[:10]
    hor_fim = str(body.get("hor_fim") or "").strip()
    if not hor_fim:
        return GuiaError(
            "Informe a CHEGADA real do trecho para concluir.",
            "chegada_obrigatoria",
        )
    if not _horario_valido(hor_fim):
        return GuiaError("CHEGADA do trecho inválida.", "validacao")
    fim_dt = _datetime_guia(data_sql, hor_fim)
    if fim_dt is None:
        return GuiaError("CHEGADA do trecho inválida.", "validacao")
    err_int = _validar_intervalo_horarios(trecho.get("hor_ini"), fim_dt)
    if err_int:
        return err_int

    jae_fim = (
        _parse_id(body.get("jae_fim"), allow_zero=True)
        if "jae_fim" in body
        else _parse_id(trecho.get("jae_fim"), allow_zero=True)
    )
    rio_fim = (
        _parse_id(body.get("riocard_fim"), allow_zero=True)
        if "riocard_fim" in body
        else _parse_id(trecho.get("riocard_fim"), allow_zero=True)
    )
    # Valida totais de roleta (fim >= ini, salvo virada — aqui só inconsistência básica)
    jae_ini = _parse_id(trecho.get("jae_ini"), allow_zero=True)
    if jae_ini is not None and jae_fim is not None and jae_fim < jae_ini and not body.get("virada_jae"):
        return GuiaError(
            "Leitura Ja E final menor que a inicial. Informe virada ou corrija.",
            "leitura_invalida",
        )
    rio_ini = _parse_id(trecho.get("riocard_ini"), allow_zero=True)
    if rio_ini is not None and rio_fim is not None and rio_fim < rio_ini and not body.get("virada_riocard"):
        return GuiaError(
            "Leitura RioCard final menor que a inicial. Informe virada ou corrija.",
            "leitura_invalida",
        )

    versao_atual = _versao(trecho)
    ok = dal.update(
        """
        UPDATE tb_guia_trecho
        SET status = ?, hor_fim = ?,
            jae_fim = COALESCE(?, jae_fim),
            riocard_fim = COALESCE(?, riocard_fim),
            id_usuario = ?, atualizado_em = ?,
            versao = COALESCE(versao, 1) + 1
        WHERE id_trecho = ?
          AND UPPER(TRIM(COALESCE(status, ''))) = ?
          AND COALESCE(versao, 1) = ?
        """,
        (
            TRECHO_CONCLUIDO,
            fim_dt,
            jae_fim,
            rio_fim,
            int(id_usuario),
            _agora(),
            int(id_trecho),
            TRECHO_EM_TRANSITO,
            versao_atual,
        ),
    )
    if not ok:
        return GuiaError(
            "Não foi possível concluir o trecho (conflito ou status inválido).",
            "conflito_versao",
        )

    err_a = _registrar_auditoria(
        dal,
        entidade="trecho",
        id_entidade=int(id_trecho),
        id_guia=id_guia,
        id_usuario=int(id_usuario),
        campo="status",
        valor_anterior=st,
        valor_novo=TRECHO_CONCLUIDO,
        motivo=str(body.get("motivo") or "Conclusão do trecho"),
    )
    if err_a:
        return err_a

    for t in listar_trechos(dal, id_guia):
        if int(t.get("id_trecho") or 0) == int(id_trecho):
            return t
    return GuiaError("Trecho não encontrado.", "nao_encontrado")


def cancelar_trecho(
    dal, id_trecho: int, body: dict[str, Any], id_usuario: int
) -> dict[str, Any] | GuiaError:
    """Cancela trecho → libera motorista e carro; Guia permanece ABERTA."""
    df = dal.read(
        "SELECT * FROM tb_guia_trecho WHERE id_trecho = ?",
        (int(id_trecho),),
    )
    if df is None or getattr(df, "empty", True):
        return GuiaError("Trecho não encontrado.", "nao_encontrado")
    trecho = df.iloc[0].to_dict()
    err_v = _checar_versao(trecho, body)
    if err_v:
        return err_v

    id_guia = int(trecho["id_guia"])
    guia = _row_guia(dal, id_guia)
    if not guia:
        return GuiaError("Guia não encontrada.", "nao_encontrado")
    if _status_guia(guia) != STATUS_ABERTA:
        return GuiaError("Guia encerrada.", "guia_encerrada")

    st = _status_trecho(trecho)
    if st == TRECHO_CANCELADO:
        return _enriquecer_trecho(trecho)
    if st == TRECHO_CONCLUIDO:
        return GuiaError("Trecho já concluído não pode ser cancelado.", "trecho_concluido")

    motivo = str(body.get("motivo") or body.get("justificativa") or "").strip()
    if len(motivo) < 5:
        return GuiaError(
            "Informe o motivo do cancelamento (mín. 5 caracteres).",
            "motivo_obrigatorio",
        )

    versao_atual = _versao(trecho)
    ok = dal.update(
        """
        UPDATE tb_guia_trecho
        SET status = ?, atualizado_em = ?, id_usuario = ?,
            versao = COALESCE(versao, 1) + 1
        WHERE id_trecho = ?
          AND COALESCE(versao, 1) = ?
          AND UPPER(TRIM(COALESCE(status, ''))) IN (?, ?)
        """,
        (
            TRECHO_CANCELADO,
            _agora(),
            int(id_usuario),
            int(id_trecho),
            versao_atual,
            TRECHO_PLANEJADO,
            TRECHO_EM_TRANSITO,
        ),
    )
    if not ok:
        return GuiaError(
            "Não foi possível cancelar o trecho (conflito de versão).",
            "conflito_versao",
        )

    err_a = _registrar_auditoria(
        dal,
        entidade="trecho",
        id_entidade=int(id_trecho),
        id_guia=id_guia,
        id_usuario=int(id_usuario),
        campo="status",
        valor_anterior=st,
        valor_novo=TRECHO_CANCELADO,
        motivo=motivo,
    )
    if err_a:
        return err_a

    for t in listar_trechos(dal, id_guia):
        if int(t.get("id_trecho") or 0) == int(id_trecho):
            return t
    return GuiaError("Trecho não encontrado.", "nao_encontrado")


def excluir_trecho(
    dal, id_trecho: int, body: dict[str, Any] | None, id_usuario: int
) -> GuiaError | None:
    """
    Exclui trecho PENDENTE (PLANEJADO sem SAÍDA).
    EM_TRANSITO deve ser cancelado com motivo; CONCLUIDO só corrige com auditoria.
    """
    del id_usuario  # reservado para auditoria futura de exclusão
    body = body or {}
    df = dal.read(
        "SELECT * FROM tb_guia_trecho WHERE id_trecho = ?",
        (int(id_trecho),),
    )
    if df is None or getattr(df, "empty", True):
        return GuiaError("Trecho não encontrado.", "nao_encontrado")
    trecho = df.iloc[0].to_dict()
    err_v = _checar_versao(trecho, body)
    if err_v:
        return err_v

    id_guia = int(trecho["id_guia"])
    guia = _row_guia(dal, id_guia)
    if not guia:
        return GuiaError("Guia não encontrada.", "nao_encontrado")
    if _status_guia(guia) != STATUS_ABERTA:
        return GuiaError("Guia encerrada.", "guia_encerrada")

    st = _status_trecho(trecho)
    if st == TRECHO_EM_TRANSITO:
        return GuiaError(
            "Trecho em trânsito não pode ser excluído. Cancele informando o motivo.",
            "trecho_em_transito",
        )
    if st == TRECHO_CONCLUIDO:
        return GuiaError(
            "Trecho concluído não pode ser excluído. Corrija com motivo e auditoria.",
            "trecho_concluido",
        )
    if st == TRECHO_CANCELADO:
        return GuiaError("Trecho já cancelado.", "trecho_cancelado")
    if trecho.get("hor_ini"):
        return GuiaError(
            "Trecho com SAÍDA registrada não pode ser excluído. Cancele com motivo.",
            "trecho_com_saida",
        )

    ok = dal.delete(
        "DELETE FROM tb_guia_trecho WHERE id_trecho = ?",
        (int(id_trecho),),
    )
    if not ok:
        return GuiaError("Falha ao excluir trecho.", "persistencia")
    return None


def registrar_troca_recurso(
    dal, id_guia: int, body: dict[str, Any], id_usuario: int
) -> dict[str, Any] | GuiaError:
    """
    Troca linha/carro/rota sem encerrar a Guia (mesma empresa).
    Atualiza snapshot do cabeçalho e grava auditoria.
    """
    guia = _row_guia(dal, int(id_guia))
    if not guia:
        return GuiaError("Guia não encontrada.", "nao_encontrado")
    if _status_guia(guia) != STATUS_ABERTA:
        return GuiaError("Guia encerrada.", "guia_encerrada")

    # Não troca recursos com trecho em trânsito (trava motorista/carro)
    em = dal.read(
        """
        SELECT id_trecho FROM tb_guia_trecho
        WHERE id_guia = ? AND UPPER(TRIM(COALESCE(status, ''))) = ?
        LIMIT 1
        """,
        (int(id_guia), TRECHO_EM_TRANSITO),
    )
    if em is not None and not getattr(em, "empty", True):
        return GuiaError(
            "Há trecho em trânsito. Conclua ou cancele antes de trocar linha/carro.",
            "trecho_em_transito",
        )

    campo = str(body.get("campo") or "").strip().lower()
    if campo not in CAMPOS_ALTERACAO:
        return GuiaError("Campo inválido. Use linha, veiculo ou rota.", "validacao")
    motivo = str(body.get("motivo") or body.get("justificativa") or "").strip()
    if len(motivo) < 5:
        return GuiaError("Informe o motivo da troca (mín. 5 caracteres).", "validacao")

    id_empresa = guia.get("id_empresa")
    valor_anterior = None
    valor_novo = None
    id_linha_novo = None
    id_veiculo_novo = None

    if campo == "veiculo":
        valor_anterior = str(guia.get("numero_frota") or guia.get("id_veiculo") or "")
        id_veiculo_novo = _parse_id(body.get("id_veiculo"))
        frota = str(body.get("numero_frota") or body.get("carro") or body.get("valor_novo") or "").strip()
        if not id_veiculo_novo and frota:
            id_veiculo_novo = _id_veiculo_por_frota(dal, frota)
        if not id_veiculo_novo:
            return GuiaError("Informe o novo carro.", "validacao")
        vei = dal.read(
            "SELECT id_veiculo, numero_frota, ativo FROM tb_veiculo WHERE id_veiculo = ? AND ativo = 1",
            (int(id_veiculo_novo),),
        )
        if vei is None or vei.empty:
            return GuiaError("Carro não encontrado.", "carro_invalido")
        valor_novo = str(vei.iloc[0].get("numero_frota") or id_veiculo_novo)
        dal.update(
            "UPDATE tb_guia SET id_veiculo = ?, versao = COALESCE(versao, 1) + 1 WHERE id_guia = ?",
            (int(id_veiculo_novo), int(id_guia)),
        )

    elif campo == "linha":
        valor_anterior = str(
            guia.get("linha_codigo") or guia.get("linha_descricao") or guia.get("id_linha") or ""
        )
        id_linha_novo = _parse_id(body.get("id_linha") or body.get("valor_novo"))
        if not id_linha_novo:
            return GuiaError("Informe a nova linha.", "validacao")
        lin = dal.read(
            "SELECT id_linha, codigo_linha, descricao, id_empresa FROM tb_linha WHERE id_linha = ? AND ativo = 1",
            (int(id_linha_novo),),
        )
        if lin is None or lin.empty:
            return GuiaError("Linha não encontrada.", "linha_invalida")
        if id_empresa is not None and lin.iloc[0].get("id_empresa") is not None:
            if int(lin.iloc[0]["id_empresa"]) != int(id_empresa):
                return GuiaError(
                    "Troca para outra empresa não é permitida nesta guia. "
                    "Encerre a jornada e abra nova guia na empresa destino.",
                    "empresa_diferente",
                )
        valor_novo = str(lin.iloc[0].get("codigo_linha") or id_linha_novo)
        dal.update(
            "UPDATE tb_guia SET id_linha = ?, versao = COALESCE(versao, 1) + 1 WHERE id_guia = ?",
            (int(id_linha_novo), int(id_guia)),
        )

    else:  # rota
        valor_anterior = str(body.get("valor_anterior") or "")
        valor_novo = str(body.get("valor_novo") or "").strip()
        if not valor_novo:
            return GuiaError("Informe a nova rota.", "validacao")

    ok = dal.create(
        """
        INSERT INTO tb_guia_alteracao (
            id_guia, id_usuario, campo, valor_anterior, valor_novo, motivo, registrado_em
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            int(id_guia),
            int(id_usuario),
            campo,
            valor_anterior,
            valor_novo,
            motivo[:255],
            _agora(),
        ),
    )
    if not ok:
        return GuiaError("Falha ao registrar alteração.", "persistencia")

    return obter_guia_completa(dal, int(id_guia))


def encerrar_guia(
    dal, id_guia: int, body: dict[str, Any] | None = None, id_usuario: Optional[int] = None
) -> dict[str, Any] | GuiaError:
    body = body or {}
    guia = _row_guia(dal, int(id_guia))
    if not guia:
        return GuiaError("Guia não encontrada.", "nao_encontrado")
    if _status_guia(guia) == STATUS_ENCERRADA:
        return obter_guia_completa(dal, int(id_guia))

    err_v = _checar_versao(guia, body)
    if err_v:
        return err_v

    motivo_tipo = str(body.get("motivo_tipo") or body.get("tipo") or "fim_jornada").strip().lower()
    if motivo_tipo not in MOTIVOS_ENCERRAMENTO:
        return GuiaError(
            "Encerramento permitido apenas por fim_jornada ou transferencia_empresa.",
            "validacao",
        )
    motivo = str(body.get("motivo") or body.get("justificativa") or "").strip()
    if motivo_tipo == "transferencia_empresa" and len(motivo) < 5:
        return GuiaError(
            "Informe o motivo da transferência de empresa (mín. 5 caracteres).",
            "motivo_obrigatorio",
        )

    data_sql = str(guia.get("hor_ini") or guia.get("data") or "")[:10]
    if len(data_sql) < 10:
        return GuiaError("Data da guia inválida.", "validacao")

    # Impede encerrar com trecho em trânsito
    em = dal.read(
        """
        SELECT id_trecho FROM tb_guia_trecho
        WHERE id_guia = ?
          AND UPPER(TRIM(COALESCE(status, ''))) = ?
        LIMIT 1
        """,
        (int(id_guia), TRECHO_EM_TRANSITO),
    )
    if em is not None and not getattr(em, "empty", True):
        return GuiaError(
            "Há trecho em trânsito. Conclua ou cancele antes de encerrar a guia.",
            "trecho_em_transito",
        )

    hor_fim = str(body.get("hor_fim") or body.get("horario_largada") or "").strip()
    if not hor_fim:
        hor_fim = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if not _horario_valido(hor_fim):
        return GuiaError("FIM(JORNADA) inválido.", "validacao")

    fim_dt = _datetime_guia(data_sql, hor_fim)
    err_int = _validar_intervalo_horarios(guia.get("hor_ini"), fim_dt)
    if err_int:
        return err_int

    if id_usuario is not None:
        err_a = _registrar_auditoria(
            dal,
            entidade="guia",
            id_entidade=int(id_guia),
            id_guia=int(id_guia),
            id_usuario=int(id_usuario),
            campo="status",
            valor_anterior=_status_guia(guia),
            valor_novo=STATUS_ENCERRADA,
            motivo=motivo or f"Encerramento: {motivo_tipo}",
        )
        if err_a:
            return err_a

    ok = dal.update(
        """
        UPDATE tb_guia
        SET hor_fim = ?, status = ?, versao = COALESCE(versao, 1) + 1
        WHERE id_guia = ?
        """,
        (fim_dt, STATUS_ENCERRADA, int(id_guia)),
    )
    if not ok:
        return GuiaError("Falha ao encerrar guia.", "persistencia")
    return obter_guia_completa(dal, int(id_guia))


def validar_abertura_jornada(
    dal,
    *,
    id_motorista: Optional[int],
    id_empresa: Optional[int],
    data_sql: str,
) -> GuiaError | None:
    """Regras de unicidade da jornada aberta por motorista/empresa/data."""
    if not id_motorista:
        return None

    disp = disponibilidade_motorista(dal, int(id_motorista), data_sql=data_sql)
    if disp["disponibilidade"] == MOT_EM_TRANSITO:
        return GuiaError(
            f"Motorista em trânsito (guia {disp.get('numero_guia')}). "
            "Conclua o trecho antes de abrir nova guia.",
            "motorista_em_transito",
        )
    if disp["disponibilidade"] == MOT_DISPONIVEL:
        # Pode só receber próximo trecho na mesma guia — não abrir paralela
        id_guia_aberta = disp.get("id_guia_aberta")
        id_emp_aberta = disp.get("id_empresa")
        if id_empresa is not None and id_emp_aberta is not None:
            if int(id_emp_aberta) != int(id_empresa):
                return GuiaError(
                    f"Motorista possui guia aberta ({disp.get('numero_guia')}) em outra empresa. "
                    "Encerre a jornada atual antes de abrir guia na empresa destino.",
                    "empresa_diferente",
                )
        return GuiaError(
            f"Já existe guia aberta ({disp.get('numero_guia')}) para este motorista. "
            "Use a mesma guia para o próximo trecho — não abra guia paralela.",
            "guia_aberta",
        )

    # Já aberta na mesma empresa/data (fallback)
    if id_empresa is not None:
        mesma = _guia_aberta_motorista(
            dal, int(id_motorista), data_sql, id_empresa=int(id_empresa)
        )
        if mesma:
            return GuiaError(
                f"Já existe guia aberta ({mesma.get('numero')}) para este motorista "
                "nesta empresa e data.",
                "guia_aberta",
            )

    # Aberta em outra empresa → deve encerrar antes
    outra = dal.read(
        """
        SELECT id_guia, id_empresa, numero
        FROM tb_guia
        WHERE id_motorista = ?
          AND DATE(COALESCE(hor_ini, data)) = ?
          AND UPPER(TRIM(COALESCE(status, 'ABERTA'))) = ?
          AND hor_fim IS NULL
          AND (id_empresa IS NULL OR id_empresa <> ?)
        ORDER BY id_guia DESC LIMIT 1
        """,
        (
            int(id_motorista),
            data_sql,
            STATUS_ABERTA,
            int(id_empresa) if id_empresa is not None else -1,
        ),
    )
    if outra is not None and not getattr(outra, "empty", True):
        num = outra.iloc[0].get("numero")
        return GuiaError(
            f"Motorista possui guia aberta ({num}) em outra empresa. "
            "Encerre a jornada atual antes de abrir guia na empresa destino.",
            "empresa_diferente",
        )
    return None

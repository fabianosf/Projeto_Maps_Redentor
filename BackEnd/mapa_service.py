# ----------------------------
# Deus seja Louvado!
# ----------------------------

"""Regras de negócio do módulo MAPA — RF-MAP-RN-001..008."""

from __future__ import annotations

import logging
import math
import re
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from typing import Any, Optional
from zoneinfo import ZoneInfo

from .cadastros_service import CadastroError, criar_veiculo
from .constants import COD_MAP_INSERT_RETRIES, COD_MAP_MAX, PERFIL_ADMIN

logger = logging.getLogger(__name__)

STATUS_ESCALA_EM_ANDAMENTO = "EM_ANDAMENTO"
STATUS_ESCALA_ENCERRADA = "ENCERRADA"
TZ_OPERACIONAL = ZoneInfo("America/Sao_Paulo")


def _agora_operacional() -> datetime:
    """Agora no fuso operacional (naive local America/Sao_Paulo)."""
    return datetime.now(TZ_OPERACIONAL).replace(tzinfo=None, second=0, microsecond=0)

# Sequence/contador atômico de cod_map (única global). Não usar MAX+1 sem lock.
_COD_MAP_SEQ_NAME = "tb_map_cod_map_seq"
_COD_MAP_COUNTER_TABLE = "tb_cod_map_seq"
_COD_MAP_COUNTER_ID = 1
_cod_map_gerador_pronto = False


@dataclass(frozen=True)
class MapaError:
    mensagem: str
    codigo: str = "mapa_erro"


def _parse_date(value: Any) -> date | MapaError:
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    texto = str(value or "").strip()
    if not texto:
        return MapaError("Data é obrigatória.", "validacao")
    for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(texto, fmt).date()
        except ValueError:
            continue
    return MapaError("Data inválida.", "validacao")


def _parse_datetime(value: Any) -> datetime | MapaError:
    if isinstance(value, datetime):
        return value
    texto = str(value or "").strip()
    if not texto:
        return MapaError("Data/hora é obrigatória.", "validacao")
    for fmt in (
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%d/%m/%Y %H:%M",
    ):
        try:
            return datetime.strptime(texto, fmt)
        except ValueError:
            continue
    return MapaError("Data/hora inválida.", "validacao")


def _parse_datetime_optional(value: Any) -> datetime | None | MapaError:
    """FIM DE JORNADA — aceita vazio/null (legado). Preferir `_parse_hora_plantao`."""
    if value is None:
        return None
    texto = str(value).strip()
    if not texto or texto.lower() in ("null", "none"):
        return None
    return _parse_datetime(texto)


def _parse_hora_plantao(
    value: Any, *, obrigatorio: bool = True
) -> time | None | MapaError:
    """
    Aceita HH:mm / HH:mm:ss ou datetime legado; devolve time puro (00:00–23:59).
    Rejeita horas inexistentes (24:00, 12:99, 99, texto livre).
    """
    if isinstance(value, time) and not isinstance(value, datetime):
        return time(value.hour, value.minute, value.second)

    if isinstance(value, datetime):
        return time(value.hour, value.minute, value.second)

    if isinstance(value, timedelta):
        total = int(value.total_seconds()) % (24 * 3600)
        if total < 0:
            return MapaError(
                "Informe um horário válido no formato HH:mm.",
                "validacao",
            )
        h, rem = divmod(total, 3600)
        m, s = divmod(rem, 60)
        return time(h, m, s)

    if value is None:
        if obrigatorio:
            return MapaError(
                "Informe um horário válido no formato HH:mm.",
                "validacao",
            )
        return None

    texto = str(value).strip()
    if not texto or texto.lower() in ("null", "none", "nan"):
        if obrigatorio:
            return MapaError(
                "Informe um horário válido no formato HH:mm.",
                "validacao",
            )
        return None

    # HH:mm ou HH:mm:ss estrito
    m = re.fullmatch(r"(\d{2}):(\d{2})(?::(\d{2}))?", texto)
    if m:
        hh, mm = int(m.group(1)), int(m.group(2))
        ss = int(m.group(3) or 0)
        if hh > 23 or mm > 59 or ss > 59:
            return MapaError(
                "Informe um horário válido no formato HH:mm.",
                "validacao",
            )
        return time(hh, mm, ss)

    # Legado: datetime embutido — extrai a hora
    parsed_dt = _parse_datetime(texto)
    if isinstance(parsed_dt, datetime):
        return time(parsed_dt.hour, parsed_dt.minute, parsed_dt.second)

    return MapaError(
        "Informe um horário válido no formato HH:mm.",
        "validacao",
    )


def _formatar_hora_api(value: Any) -> str | None:
    """Normaliza valor de plantão para HH:mm na resposta da API."""
    hora = _parse_hora_plantao(value, obrigatorio=False)
    if hora is None or isinstance(hora, MapaError):
        return None
    return f"{hora.hour:02d}:{hora.minute:02d}"


def _hora_plantao_sql(hora: time, data_mapa: date, dal) -> str:
    """PostgreSQL: TIME. Demais SGBDs: DATETIME combinado com a data do MAPA."""
    sgbd = _dal_sgbd(dal)
    if sgbd == "postgresql":
        return hora.strftime("%H:%M:%S")
    return datetime.combine(data_mapa, hora).strftime("%Y-%m-%d %H:%M:%S")


def _validar_plantao(inicio: time, fim: time) -> MapaError | None:
    """Plantão no mesmo dia civil: fim deve ser estritamente após o início."""
    if (fim.hour, fim.minute, fim.second) <= (
        inicio.hour,
        inicio.minute,
        inicio.second,
    ):
        return MapaError(
            "Início do plantão deve ser anterior ao fim.",
            "validacao",
        )
    return None


def _garantir_locais_padrao(dal) -> tuple[int, int] | MapaError:
    """Garante 2 locais para FK de tb_linha."""
    existentes = dal.read(
        "SELECT id_local, codigo_local FROM tb_local WHERE ativo = 1 ORDER BY codigo_local"
    )
    ids: list[int] = []
    if not existentes.empty:
        ids = [int(r["id_local"]) for _, r in existentes.iterrows()]
    while len(ids) < 2:
        codigo = 10 + len(ids) * 10
        ok = dal.create(
            "INSERT INTO tb_local (codigo_local, descricao, ativo) VALUES (?, ?, 1)",
            (codigo, f"Local {codigo}"),
        )
        if not ok:
            return MapaError("Falha ao preparar locais da linha.", "persistencia")
        row = dal.read(
            "SELECT id_local FROM tb_local WHERE codigo_local = ?",
            (codigo,),
        )
        if row.empty:
            return MapaError("Falha ao preparar locais da linha.", "persistencia")
        ids.append(int(row.iloc[0]["id_local"]))
    return ids[0], ids[1]


def _id_pk_informado(valor: Any) -> bool:
    """True se o cliente enviou PK (inclui 0 — seeds usam id a partir de zero)."""
    return valor is not None and valor != ""


def _resolver_id_empresa(dal, payload: dict[str, Any]) -> int | None:
    """Resolve id_empresa por PK, codigo_empresa ou descricao (campo empresa)."""
    id_empresa = payload.get("id_empresa")
    if _id_pk_informado(id_empresa):
        empresa = dal.read(
            "SELECT id_empresa FROM tb_empresa WHERE id_empresa = ? AND ativo = 1",
            (int(id_empresa),),
        )
        if empresa.empty and int(id_empresa) != 0:
            empresa = dal.read(
                "SELECT id_empresa FROM tb_empresa WHERE codigo_empresa = ? AND ativo = 1",
                (int(id_empresa),),
            )
        if not empresa.empty:
            return int(empresa.iloc[0]["id_empresa"])

    descricao = str(payload.get("empresa") or "").strip()
    if descricao:
        empresa = dal.read(
            """
            SELECT id_empresa FROM tb_empresa
            WHERE LOWER(TRIM(descricao)) = LOWER(?) AND ativo = 1
            """,
            (descricao,),
        )
        if not empresa.empty:
            return int(empresa.iloc[0]["id_empresa"])

        # Cria sob demanda (combo UI: Futuro/Redentor/Barra) alinhado ao seed.
        codigos_conhecidos = {"redentor": 1, "futuro": 2, "barra": 3}
        codigo = codigos_conhecidos.get(descricao.lower())
        if codigo is None:
            max_df = dal.read(
                "SELECT COALESCE(MAX(codigo_empresa), 0) AS max_cod FROM tb_empresa"
            )
            codigo = int(max_df.iloc[0]["max_cod"]) + 1
        ok = dal.create(
            """
            INSERT INTO tb_empresa (codigo_empresa, descricao, ativo)
            VALUES (?, ?, 1)
            """,
            (codigo, descricao),
        )
        if not ok:
            return None
        criada = dal.read(
            """
            SELECT id_empresa FROM tb_empresa
            WHERE LOWER(TRIM(descricao)) = LOWER(?) AND ativo = 1
            """,
            (descricao,),
        )
        if not criada.empty:
            return int(criada.iloc[0]["id_empresa"])

    return None


def _resolver_id_turno(dal, payload: dict[str, Any]) -> int | MapaError:
    id_turno = payload.get("id_turno")
    if _id_pk_informado(id_turno):
        turno = dal.read(
            "SELECT id_turno FROM tb_turno WHERE id_turno = ? AND ativo = 1",
            (int(id_turno),),
        )
        if not turno.empty:
            return int(turno.iloc[0]["id_turno"])
        # tenta por codigo_turno igual ao valor enviado (exceto 0, que é PK válida)
        if int(id_turno) != 0:
            turno = dal.read(
                "SELECT id_turno FROM tb_turno WHERE codigo_turno = ? AND ativo = 1",
                (int(id_turno),),
            )
            if not turno.empty:
                return int(turno.iloc[0]["id_turno"])

    codigo = payload.get("codigo_turno")
    if codigo not in (None, ""):
        turno = dal.read(
            "SELECT id_turno FROM tb_turno WHERE codigo_turno = ? AND ativo = 1",
            (int(codigo),),
        )
        if not turno.empty:
            return int(turno.iloc[0]["id_turno"])

    descricao = str(payload.get("turno") or "").strip().upper()
    if descricao:
        turno = dal.read(
            "SELECT id_turno FROM tb_turno WHERE UPPER(TRIM(descricao)) = ? AND ativo = 1",
            (descricao,),
        )
        if not turno.empty:
            return int(turno.iloc[0]["id_turno"])

    return MapaError("Turno inválido ou inativo.", "validacao")


def _resolver_id_linha(dal, payload: dict[str, Any]) -> int | MapaError:
    """Resolve id_linha por PK, codigo_linha ou cria a linha sob demanda."""
    id_linha = payload.get("id_linha")
    if _id_pk_informado(id_linha):
        linha = dal.read(
            "SELECT id_linha FROM tb_linha WHERE id_linha = ? AND ativo = 1",
            (int(id_linha),),
        )
        if not linha.empty:
            return int(linha.iloc[0]["id_linha"])

    codigo_raw = payload.get("codigo_linha")
    if codigo_raw in (None, ""):
        return MapaError("Linha é obrigatória.", "validacao")
    try:
        codigo_int = int(str(codigo_raw).strip())
    except (TypeError, ValueError):
        return MapaError("Linha inválida.", "validacao")
    if codigo_int <= 0:
        return MapaError("Linha inválida.", "validacao")

    id_empresa_ok = _resolver_id_empresa(dal, payload)
    if id_empresa_ok is None:
        return MapaError("Empresa é obrigatória para cadastrar a linha.", "validacao")

    existente = dal.read(
        """
        SELECT id_linha FROM tb_linha
        WHERE codigo_linha = ? AND id_empresa = ? AND ativo = 1
        """,
        (codigo_int, id_empresa_ok),
    )
    if not existente.empty:
        return int(existente.iloc[0]["id_linha"])

    locais = _garantir_locais_padrao(dal)
    if isinstance(locais, MapaError):
        return locais
    id_origem, id_destino = locais

    descricao = str(codigo_int).zfill(3)
    ok = dal.create(
        """
        INSERT INTO tb_linha (
            codigo_linha, id_empresa, descricao,
            id_local_origem, id_local_destino, ativo
        ) VALUES (?, ?, ?, ?, ?, 1)
        """,
        (codigo_int, id_empresa_ok, descricao, id_origem, id_destino),
    )
    if not ok:
        # Corrida / UNIQUE (id_empresa, codigo_linha)
        existente = dal.read(
            """
            SELECT id_linha FROM tb_linha
            WHERE codigo_linha = ? AND id_empresa = ?
            """,
            (codigo_int, id_empresa_ok),
        )
        if not existente.empty:
            return int(existente.iloc[0]["id_linha"])
        return MapaError("Falha ao cadastrar a linha.", "persistencia")

    criada = dal.read(
        """
        SELECT id_linha FROM tb_linha
        WHERE codigo_linha = ? AND id_empresa = ?
        """,
        (codigo_int, id_empresa_ok),
    )
    if criada.empty:
        return MapaError("Falha ao cadastrar a linha.", "persistencia")
    return int(criada.iloc[0]["id_linha"])


class _AbortMapaTx(Exception):
    """Aborta transação de MAPA carregando MapaError (rollback no DAL)."""

    def __init__(self, erro: MapaError) -> None:
        self.erro = erro
        super().__init__(erro.mensagem)


def _dal_sgbd(dal) -> str:
    getter = getattr(dal, "get_sgbd", None)
    if callable(getter):
        return str(getter() or "").strip().lower()
    return str(getattr(dal, "sgbd", "") or "").strip().lower()


def _is_unique_violation(exc: BaseException) -> bool:
    """Detecta unique violation (PostgreSQL 23505 / MySQL 1062 / SQLite)."""
    pgcode = getattr(exc, "pgcode", None)
    if pgcode == "23505":
        return True
    sqlstate = getattr(exc, "sqlstate", None)
    if sqlstate == "23505":
        return True
    name = type(exc).__name__
    msg = str(exc).lower()
    if name in {"UniqueViolation", "IntegrityError"} and (
        "unique" in msg
        or "duplicate" in msg
        or "23505" in msg
        or "1062" in msg
    ):
        return True
    if "duplicate key" in msg or "unique constraint" in msg or "1062" in msg:
        return True
    cause = getattr(exc, "__cause__", None) or getattr(exc, "orig", None)
    if cause is not None and cause is not exc:
        return _is_unique_violation(cause)
    return False


def _max_cod_map_existente(dal) -> int:
    """Piso histórico para sync da sequence — não é fonte de unicidade."""
    df = dal.read("SELECT COALESCE(MAX(cod_map), 0) AS max_cod FROM tb_map")
    if df is None or df.empty:
        return 0
    try:
        return int(df.iloc[0]["max_cod"] or 0)
    except (TypeError, ValueError):
        return 0


def _executar_ddl(dal, sql: str) -> None:
    if hasattr(dal, "execute_query"):
        dal.execute_query(sql, fetch=False)
        return
    # SqliteTestDal / stubs: create cobre DDL simples
    dal.create(sql)


def _sync_cod_map_seq_postgresql(dal) -> None:
    max_cod = _max_cod_map_existente(dal)
    if max_cod < 1:
        dal.read(f"SELECT setval('{_COD_MAP_SEQ_NAME}', 1, false) AS s")
    else:
        dal.read(
            f"SELECT setval('{_COD_MAP_SEQ_NAME}', ?, true) AS s",
            (max_cod,),
        )


def _assegurar_gerador_cod_map(dal, *, force_sync: bool = False) -> None:
    """Cria sequence/contador e alinha ao maior cod_map já existente.

    Sem lock de processo: evita deadlock com `dal.transaction()` (ex.: SQLite RLock).
    Unicidade vem de nextval / FOR UPDATE + UNIQUE(cod_map) com retry.
    """
    global _cod_map_gerador_pronto
    sgbd = _dal_sgbd(dal)
    if sgbd == "postgresql":
        if _cod_map_gerador_pronto and not force_sync:
            return
        _executar_ddl(
            dal,
            f"""
            CREATE SEQUENCE IF NOT EXISTS {_COD_MAP_SEQ_NAME}
                AS INTEGER
                INCREMENT BY 1
                MINVALUE 1
                NO CYCLE
            """,
        )
        _sync_cod_map_seq_postgresql(dal)
        _cod_map_gerador_pronto = True
        return

    _executar_ddl(
        dal,
        f"""
        CREATE TABLE IF NOT EXISTS {_COD_MAP_COUNTER_TABLE} (
            id INTEGER NOT NULL PRIMARY KEY,
            ultimo_seq INTEGER NOT NULL DEFAULT 0
        )
        """,
    )
    row = dal.read(
        f"SELECT ultimo_seq FROM {_COD_MAP_COUNTER_TABLE} WHERE id = ?",
        (_COD_MAP_COUNTER_ID,),
    )
    max_cod = _max_cod_map_existente(dal)
    if row is None or row.empty:
        dal.create(
            f"""
            INSERT INTO {_COD_MAP_COUNTER_TABLE} (id, ultimo_seq)
            VALUES (?, ?)
            """,
            (_COD_MAP_COUNTER_ID, max_cod),
        )
        return
    try:
        atual = int(row.iloc[0]["ultimo_seq"] or 0)
    except (TypeError, ValueError):
        atual = 0
    if force_sync or max_cod > atual:
        dal.update(
            f"""
            UPDATE {_COD_MAP_COUNTER_TABLE}
            SET ultimo_seq = ?
            WHERE id = ?
            """,
            (max(max_cod, atual), _COD_MAP_COUNTER_ID),
        )


def _gerar_proximo_cod_map(dal) -> int | MapaError:
    """
    Próximo cod_map atômico.
    PostgreSQL: nextval(sequence). Demais SGBDs: contador com FOR UPDATE.
    """
    _assegurar_gerador_cod_map(dal)
    sgbd = _dal_sgbd(dal)

    if sgbd == "postgresql":
        df = dal.read(f"SELECT nextval('{_COD_MAP_SEQ_NAME}') AS n")
        if df is None or df.empty:
            return MapaError("Falha ao gerar código do MAPA.", "persistencia")
        try:
            proximo = int(df.iloc[0]["n"])
        except (TypeError, ValueError):
            return MapaError("Falha ao gerar código do MAPA.", "persistencia")
        if proximo > COD_MAP_MAX:
            return MapaError("Limite de cod_map esgotado.", "cod_map_esgotado")
        return proximo

    locked = dal.read(
        f"""
        SELECT ultimo_seq FROM {_COD_MAP_COUNTER_TABLE}
        WHERE id = ? FOR UPDATE
        """,
        (_COD_MAP_COUNTER_ID,),
    )
    if locked is None or locked.empty:
        return MapaError("Falha ao inicializar sequência de cod_map.", "persistencia")
    try:
        ultimo = int(locked.iloc[0]["ultimo_seq"] or 0)
    except (TypeError, ValueError):
        return MapaError("Sequência de cod_map inválida.", "persistencia")
    # Piso histórico sob lock (dados antigos); unicidade vem do incremento bloqueado.
    piso = _max_cod_map_existente(dal)
    proximo = max(ultimo, piso) + 1
    if proximo > COD_MAP_MAX:
        return MapaError("Limite de cod_map esgotado.", "cod_map_esgotado")
    ok = dal.update(
        f"""
        UPDATE {_COD_MAP_COUNTER_TABLE}
        SET ultimo_seq = ?
        WHERE id = ?
        """,
        (proximo, _COD_MAP_COUNTER_ID),
    )
    if not ok:
        return MapaError("Falha ao atualizar sequência de cod_map.", "persistencia")
    return proximo


def _formatar_codigo_mapa(prefixo: str, seq: int) -> str:
    """Prefixo + número com no mínimo 2 dígitos (Red01 … Red99, Red100…)."""
    n = int(seq)
    width = max(2, len(str(n)))
    return f"{str(prefixo).strip()}{n:0{width}d}"


def _parse_seq_codigo_mapa(codigo: Any, prefixo: str) -> int | None:
    texto = str(codigo or "").strip()
    pref = str(prefixo or "").strip()
    if not texto or not pref:
        return None
    if not texto.lower().startswith(pref.lower()):
        return None
    suf = texto[len(pref) :]
    if not suf.isdigit():
        return None
    return int(suf)


def _limpar_codigo_mapa(valor: Any) -> str | None:
    if valor is None:
        return None
    try:
        if isinstance(valor, float) and math.isnan(valor):
            return None
    except (TypeError, ValueError):
        pass
    texto = str(valor).strip()
    if not texto or texto.lower() in ("none", "null", "nan", "nat"):
        return None
    return texto


def _json_safe_value(value: Any) -> Any:
    """Converte valores pandas/DB (Timestamp, Timedelta, NaT, date) para JSON."""
    if value is None:
        return None

    try:
        import pandas as pd

        if value is pd.NaT:
            return None
        if isinstance(value, float) and pd.isna(value):
            return None
        if isinstance(value, pd.Timedelta):
            total = int(value.total_seconds())
            if total < 0:
                return None
            # TIME do MySQL costuma vir como Timedelta do dia (ex.: 17:00).
            total = total % (24 * 3600)
            h, rem = divmod(total, 3600)
            m, s = divmod(rem, 60)
            return f"{h:02d}:{m:02d}:{s:02d}" if s else f"{h:02d}:{m:02d}"
        if isinstance(value, pd.Timestamp):
            if pd.isna(value):
                return None
            return value.to_pydatetime().strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        pass

    if isinstance(value, float) and math.isnan(value):
        return None

    if isinstance(value, timedelta):
        total = int(value.total_seconds())
        if total < 0:
            return None
        total = total % (24 * 3600)
        h, rem = divmod(total, 3600)
        m, s = divmod(rem, 60)
        return f"{h:02d}:{m:02d}:{s:02d}" if s else f"{h:02d}:{m:02d}"

    if isinstance(value, time):
        return value.strftime("%H:%M:%S") if value.second else value.strftime("%H:%M")

    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M:%S")

    if isinstance(value, date):
        return value.strftime("%Y-%m-%d")

    if isinstance(value, dict):
        return {str(k): _json_safe_value(v) for k, v in value.items()}

    if isinstance(value, (list, tuple)):
        return [_json_safe_value(v) for v in value]

    if hasattr(value, "item") and callable(getattr(value, "item", None)):
        try:
            return _json_safe_value(value.item())
        except Exception:
            pass

    if isinstance(value, (str, int, bool)):
        return value

    if isinstance(value, float):
        return value

    # Fallback seguro — nunca deixa Timedelta/objeto estranho no jsonify.
    return str(value)


def _sanitizar_mapa_payload(payload: dict[str, Any]) -> dict[str, Any]:
    safe = _json_safe_value(payload)
    if not isinstance(safe, dict):
        return {}
    if "codigo_mapa" in safe:
        safe["codigo_mapa"] = _limpar_codigo_mapa(safe.get("codigo_mapa"))
    for chave in ("inicio_jornada_des", "fim_jornada_des"):
        if chave in safe:
            safe[chave] = _formatar_hora_api(safe.get(chave))
    if "itens" not in safe or safe["itens"] is None:
        safe["itens"] = []
    elif not isinstance(safe["itens"], list):
        safe["itens"] = []
    return safe


def _rotulo_mapa(codigo_mapa: Any = None, cod_map: Any = None) -> str:
    """Rótulo de exibição: só codigo_mapa (nunca 00001)."""
    del cod_map  # id interno — não usar como código de tela
    texto = _limpar_codigo_mapa(codigo_mapa)
    return texto or "—"


def _max_seq_codigos_empresa(dal, id_empresa: int, prefixo: str) -> int:
    """Maior sufixo numérico já usado nos mapas da empresa (ainda existentes)."""
    df = dal.read(
        """
        SELECT codigo_mapa
        FROM tb_map
        WHERE id_empresa = ?
          AND codigo_mapa IS NOT NULL
        """,
        (int(id_empresa),),
    )
    max_seq = 0
    if df is None or df.empty:
        return 0
    for raw in df["codigo_mapa"].tolist():
        parsed = _parse_seq_codigo_mapa(raw, prefixo)
        if parsed is not None and parsed > max_seq:
            max_seq = parsed
    return max_seq


def _resolver_id_empresa_mapa(
    dal, payload: dict[str, Any], id_usuario: int
) -> int | MapaError:
    raw = payload.get("id_empresa")
    if raw is not None and str(raw).strip() not in ("", "null", "None"):
        try:
            id_emp = int(raw)
        except (TypeError, ValueError):
            return MapaError("Empresa inválida.", "empresa_invalida")
        emp = dal.read(
            """
            SELECT id_empresa FROM tb_empresa
            WHERE id_empresa = ? AND ativo = 1
            """,
            (id_emp,),
        )
        if emp.empty:
            return MapaError("Empresa não encontrada ou inativa.", "empresa_invalida")
        return id_emp

    usuario = dal.read(
        "SELECT id_empresa FROM tb_usuario WHERE id_usuario = ?",
        (int(id_usuario),),
    )
    if not usuario.empty and usuario.iloc[0].get("id_empresa") is not None:
        try:
            id_emp = int(usuario.iloc[0]["id_empresa"])
        except (TypeError, ValueError):
            id_emp = 0
        if id_emp > 0:
            emp = dal.read(
                """
                SELECT id_empresa FROM tb_empresa
                WHERE id_empresa = ? AND ativo = 1
                """,
                (id_emp,),
            )
            if not emp.empty:
                return id_emp

    return MapaError(
        "Empresa é obrigatória para gerar o código do MAPA.",
        "empresa_obrigatoria",
    )


def _alocar_proximo_codigo_mapa(
    dal, id_empresa: int
) -> tuple[str, int] | MapaError:
    """
    Próximo código = prefixo + sequência por empresa (ex.: Red01, Red02).

    - Com mapas vivos: max(contador persistido, maior sufixo existente) + 1
      (não reutiliza buracos após exclusão parcial).
    - Sem mapas da empresa: reinicia em 01 (contador órfão após limpeza total
      não deve gerar Red20, Red21…).
    """
    emp = dal.read(
        """
        SELECT prefixo_mapa FROM tb_empresa
        WHERE id_empresa = ? AND ativo = 1
        """,
        (int(id_empresa),),
    )
    if emp.empty:
        return MapaError("Empresa não encontrada ou inativa.", "empresa_invalida")
    prefixo = str(emp.iloc[0].get("prefixo_mapa") or "").strip()
    if not prefixo:
        return MapaError(
            "Empresa sem prefixo de mapa configurado (prefixo_mapa).",
            "prefixo_mapa_ausente",
        )

    locked = dal.read(
        "SELECT ultimo_seq FROM tb_mapa_seq WHERE id_empresa = ? FOR UPDATE",
        (int(id_empresa),),
    )
    if locked.empty:
        dal.create(
            "INSERT INTO tb_mapa_seq (id_empresa, ultimo_seq) VALUES (?, 0)",
            (int(id_empresa),),
        )
        locked = dal.read(
            "SELECT ultimo_seq FROM tb_mapa_seq WHERE id_empresa = ? FOR UPDATE",
            (int(id_empresa),),
        )
        if locked.empty:
            return MapaError(
                "Falha ao inicializar sequência do MAPA.",
                "persistencia",
            )

    try:
        seq_tabela = int(locked.iloc[0]["ultimo_seq"] or 0)
    except (TypeError, ValueError):
        return MapaError("Sequência de MAPA inválida.", "persistencia")

    seq_existente = _max_seq_codigos_empresa(dal, int(id_empresa), prefixo)
    if seq_existente <= 0:
        # Nenhum código vivo desta empresa — reinicia a numeração.
        seq = 1
    else:
        seq = max(seq_tabela, seq_existente) + 1

    ok = dal.update(
        "UPDATE tb_mapa_seq SET ultimo_seq = ? WHERE id_empresa = ?",
        (seq, int(id_empresa)),
    )
    if not ok:
        return MapaError("Falha ao atualizar sequência do MAPA.", "persistencia")

    return _formatar_codigo_mapa(prefixo, seq), seq


def listar_mapas(dal, data: str | None = None) -> list[dict[str, Any]] | MapaError:
    """Lista mapas. Filtro opcional `data` (yyyy-mm-dd ou dd/mm/aaaa) — aditivo."""
    where = ""
    params: tuple[Any, ...] | None = None
    if data is not None and str(data).strip():
        parsed = _parse_date(str(data).strip())
        if isinstance(parsed, MapaError):
            return parsed
        where = " WHERE m.data = ?"
        params = (parsed.isoformat(),)

    df = dal.read(
        f"""
        SELECT m.id_registro, m.cod_map, m.codigo_mapa, m.id_empresa AS id_empresa_map,
               m.data,
               COALESCE(e_map.descricao, e_hdr.descricao, e_item.descricao) AS empresa,
               CAST(COALESCE(l_hdr.codigo_linha, l_item.codigo_linha) AS CHAR) AS linha,
               t.descricao AS turno,
               u.nome AS despachante,
               (
                 SELECT COUNT(*)
                 FROM tb_item_map i_cnt
                 INNER JOIN tb_viagem v_cnt ON v_cnt.id_item_registro = i_cnt.id_item
                 WHERE i_cnt.idmap = m.id_registro
               ) AS total_viagens
        FROM tb_map m
        INNER JOIN tb_turno t ON t.id_turno = m.id_turno
        INNER JOIN tb_usuario u ON u.id_usuario = m.id_usuario
        LEFT JOIN tb_empresa e_map ON e_map.id_empresa = m.id_empresa
        LEFT JOIN tb_linha l_hdr ON l_hdr.id_linha = m.id_linha
        LEFT JOIN tb_empresa e_hdr ON e_hdr.id_empresa = l_hdr.id_empresa
        LEFT JOIN tb_item_map i0 ON i0.id_item = (
            SELECT MIN(i2.id_item) FROM tb_item_map i2 WHERE i2.idmap = m.id_registro
        )
        LEFT JOIN tb_linha l_item ON l_item.id_linha = i0.id_linha
        LEFT JOIN tb_empresa e_item ON e_item.id_empresa = l_item.id_empresa
        {where}
        ORDER BY m.data DESC, m.cod_map DESC
        """,
        params,
    )
    if df.empty:
        return []
    registros = df.to_dict(orient="records")
    out: list[dict[str, Any]] = []
    for row in registros:
        safe = _json_safe_value(row)
        if not isinstance(safe, dict):
            continue
        safe["codigo_mapa"] = _limpar_codigo_mapa(safe.get("codigo_mapa"))
        out.append(safe)
    return out


def obter_indicadores(
    dal, id_linha: int | None = None
) -> dict[str, Any] | MapaError:
    """
    Qtc/M — média de passageiros (ida+volta) da linha no dia atual (tb_map.data).
    Requer id_linha de tb_linha.
    """
    if id_linha is None:
        return {
            "qtc_m": None,
            "id_linha": None,
            "codigo_linha": None,
        }

    try:
        id_linha_int = int(id_linha)
    except (TypeError, ValueError):
        return MapaError("Linha inválida.", "validacao")

    linha_df = dal.read(
        """
        SELECT id_linha, codigo_linha
        FROM tb_linha
        WHERE id_linha = ? AND ativo = 1
        """,
        (id_linha_int,),
    )
    if linha_df.empty:
        return MapaError("Linha não encontrada.", "nao_encontrado")

    codigo_linha = linha_df.iloc[0]["codigo_linha"]
    try:
        codigo_exibicao = int(codigo_linha)
    except (TypeError, ValueError):
        codigo_exibicao = codigo_linha

    hoje = _agora_operacional().date().isoformat()
    df = dal.read(
        """
        SELECT AVG(
                   COALESCE(v.qtd_pas_ida, 0) + COALESCE(v.qtd_pas_volta, 0)
               ) AS qtc_m
        FROM tb_map m
        INNER JOIN tb_item_map i ON i.idmap = m.id_registro
        INNER JOIN tb_viagem v ON v.id_item_registro = i.id_item
        WHERE i.id_linha = ?
          AND m.data = ?
        """,
        (id_linha_int, hoje),
    )
    qtc_m: float | None = None
    if not df.empty and df.iloc[0]["qtc_m"] is not None:
        try:
            qtc_m = round(float(df.iloc[0]["qtc_m"]), 1)
        except (TypeError, ValueError):
            qtc_m = None

    return {
        "qtc_m": qtc_m,
        "id_linha": id_linha_int,
        "codigo_linha": codigo_exibicao,
    }


def _assegurar_codigo_mapa_registro(dal, id_registro: int) -> str | None:
    """
    Garante codigo_mapa em registro legado com id_empresa e sem código.
    Não reutiliza sequência — aloca o próximo da empresa.
    """
    row = dal.read(
        """
        SELECT id_registro, id_empresa, codigo_mapa
        FROM tb_map WHERE id_registro = ?
        """,
        (int(id_registro),),
    )
    if row is None or row.empty:
        return None
    atual = _limpar_codigo_mapa(row.iloc[0].get("codigo_mapa"))
    if atual:
        return atual
    id_emp_raw = row.iloc[0].get("id_empresa")
    try:
        if id_emp_raw is None or str(id_emp_raw).strip() in ("", "None", "nan"):
            return None
        id_emp = int(id_emp_raw)
    except (TypeError, ValueError):
        return None

    try:
        with dal.transaction():
            alocado = _alocar_proximo_codigo_mapa(dal, id_emp)
            if isinstance(alocado, MapaError):
                raise _AbortMapaTx(alocado)
            codigo, _seq = alocado
            ok = dal.update(
                """
                UPDATE tb_map
                SET codigo_mapa = ?
                WHERE id_registro = ?
                  AND (codigo_mapa IS NULL OR TRIM(codigo_mapa) = '')
                """,
                (codigo, int(id_registro)),
            )
            if not ok:
                raise _AbortMapaTx(
                    MapaError("Falha ao gravar codigo_mapa legado.", "persistencia")
                )
            return codigo
    except _AbortMapaTx:
        return None
    except Exception:
        return None


def obter_mapa_completo(dal, id_registro: int) -> dict[str, Any] | MapaError:
    cab = dal.read(
        """
        SELECT m.id_registro, m.cod_map, m.codigo_mapa, m.id_usuario, m.id_empresa,
               m.id_linha, m.id_turno, m.data, m.inicio_jornada_des, m.fim_jornada_des,
               m.observacao,
               COALESCE(m.id_empresa, l_hdr.id_empresa) AS id_empresa_resolvido,
               l_hdr.descricao AS linha,
               COALESCE(e_map.descricao, e_hdr.descricao) AS empresa,
               t.descricao AS turno,
               u.nome AS despachante,
               u.matricula AS matricula_despachante
        FROM tb_map m
        LEFT JOIN tb_turno t ON t.id_turno = m.id_turno
        LEFT JOIN tb_usuario u ON u.id_usuario = m.id_usuario
        LEFT JOIN tb_empresa e_map ON e_map.id_empresa = m.id_empresa
        LEFT JOIN tb_linha l_hdr ON l_hdr.id_linha = m.id_linha
        LEFT JOIN tb_empresa e_hdr ON e_hdr.id_empresa = l_hdr.id_empresa
        WHERE m.id_registro = ?
        """,
        (id_registro,),
    )
    if cab is None or getattr(cab, "empty", True):
        return MapaError("MAPA não encontrado.", "nao_encontrado")

    itens_df = dal.read(
        """
        SELECT i.*,
               v.numero_frota, v.placa, v.id_empresa AS id_empresa_veiculo,
               l.id_linha AS id_linha,
               l.codigo_linha,
               l.descricao AS linha,
               COALESCE(e.id_empresa, v.id_empresa) AS id_empresa,
               e.descricao AS empresa,
               mot.nome AS motorista, mot.matricula AS matricula_motorista
        FROM tb_item_map i
        LEFT JOIN tb_veiculo v ON v.id_veiculo = i.id_veiculo
        LEFT JOIN tb_linha l ON l.id_linha = i.id_linha
        LEFT JOIN tb_empresa e ON e.id_empresa = l.id_empresa
        LEFT JOIN tb_motorista mot ON mot.id_motorista = i.id_motorista
        WHERE i.idmap = ?
        ORDER BY i.id_item
        """,
        (id_registro,),
    )

    itens: list[dict[str, Any]] = []
    if itens_df is not None and not getattr(itens_df, "empty", True):
        for _, item_row in itens_df.iterrows():
            item = item_row.to_dict()
            try:
                id_item = int(item["id_item"])
            except (TypeError, ValueError, KeyError):
                logger.warning(
                    "Item de mapa com id_item inválido (mapa=%s): %s",
                    id_registro,
                    item.get("id_item"),
                )
                continue
            item["id_mapa_item"] = id_item
            st = str(item.get("status_escala") or STATUS_ESCALA_EM_ANDAMENTO).strip().upper()
            item["status_escala"] = st or STATUS_ESCALA_EM_ANDAMENTO
            _enriquecer_campos_horas_item(item)
            viagens_df = dal.read(
                """
                SELECT * FROM tb_viagem
                WHERE id_item_registro = ?
                ORDER BY id_viagem
                """,
                (id_item,),
            )
            viagens = (
                viagens_df.to_dict(orient="records")
                if viagens_df is not None and not getattr(viagens_df, "empty", True)
                else []
            )
            for v in viagens:
                try:
                    v["id_mapa_item"] = int(v.get("id_item_registro") or id_item)
                except (TypeError, ValueError):
                    v["id_mapa_item"] = id_item
            item["viagens"] = viagens
            itens.append(item)

    resultado = cab.iloc[0].to_dict()
    data_ok = _coerce_mapa_date(resultado.get("data"))
    if data_ok is not None:
        resultado["data"] = data_ok.strftime("%Y-%m-%d")

    # id_empresa canônico (evita coluna duplicada de m.*)
    id_emp_res = resultado.pop("id_empresa_resolvido", None)
    if resultado.get("id_empresa") is None and id_emp_res is not None:
        try:
            resultado["id_empresa"] = int(id_emp_res)
        except (TypeError, ValueError):
            resultado["id_empresa"] = id_emp_res

    codigo = _limpar_codigo_mapa(resultado.get("codigo_mapa"))
    id_emp_cab = resultado.get("id_empresa")
    try:
        id_emp_ok = (
            id_emp_cab is not None
            and str(id_emp_cab).strip() not in ("", "None", "nan", "0")
            and int(id_emp_cab) > 0
        )
    except (TypeError, ValueError):
        id_emp_ok = False
    if not codigo and id_emp_ok:
        try:
            codigo = _assegurar_codigo_mapa_registro(dal, int(id_registro))
        except Exception as exc:  # noqa: BLE001 — legado nunca derruba o GET
            logger.exception(
                "Falha ao assegurar codigo_mapa do mapa %s: %s", id_registro, exc
            )
            codigo = None
    resultado["codigo_mapa"] = codigo
    resultado["itens"] = itens
    return _sanitizar_mapa_payload(resultado)


def _resolver_ou_criar_veiculo_mapa(
    dal, payload: dict[str, Any], id_empresa: int
) -> int | MapaError:
    """Valida frota; cria veículo se não existir. Empresa do mapa é opcional no carro."""
    frota_raw = payload.get("numero_frota")
    if frota_raw is None or str(frota_raw).strip() == "":
        frota_raw = payload.get("veiculo")
    frota = str(frota_raw or "").strip().upper()
    if not frota:
        return MapaError("Veículo é obrigatório.", "validacao")

    existente = dal.read(
        """
        SELECT id_veiculo, id_empresa, numero_frota, ativo
        FROM tb_veiculo
        WHERE UPPER(TRIM(numero_frota)) = ?
        LIMIT 1
        """,
        (frota,),
    )
    if not existente.empty:
        row = existente.iloc[0]
        if int(row.get("ativo") or 0) not in (1, True):
            return MapaError(f"Veículo {frota} está inativo.", "validacao")
        return int(row["id_veiculo"])

    criado = criar_veiculo(dal, numero_frota=frota, id_empresa=int(id_empresa))
    if isinstance(criado, CadastroError):
        return MapaError(criado.mensagem, criado.codigo)
    return int(criado["id_veiculo"])


def criar_mapa(dal, id_usuario: int, payload: dict[str, Any]) -> dict[str, Any] | MapaError:
    """Cria cabeçalho do MAPA com codigo_mapa sequencial por empresa (ex.: Fut01)."""
    id_empresa = _resolver_id_empresa_mapa(dal, payload, id_usuario)
    if isinstance(id_empresa, MapaError):
        return id_empresa

    id_turno = _resolver_id_turno(dal, payload)
    if isinstance(id_turno, MapaError):
        return id_turno

    data_parsed = _parse_date(payload.get("data"))
    if isinstance(data_parsed, MapaError):
        return data_parsed

    inicio = _parse_hora_plantao(payload.get("inicio_jornada_des"), obrigatorio=True)
    fim = _parse_hora_plantao(payload.get("fim_jornada_des"), obrigatorio=True)
    if isinstance(inicio, MapaError):
        return inicio
    if isinstance(fim, MapaError):
        return fim
    assert isinstance(inicio, time) and isinstance(fim, time)
    err_plantao = _validar_plantao(inicio, fim)
    if err_plantao is not None:
        return err_plantao

    observacao = payload.get("observacao")
    inicio_sql = _hora_plantao_sql(inicio, data_parsed, dal)
    fim_sql = _hora_plantao_sql(fim, data_parsed, dal)

    try:
        _assegurar_gerador_cod_map(dal)
    except Exception:  # noqa: BLE001
        logger.exception("Falha ao preparar gerador de cod_map")

    last_error: MapaError | None = None
    for _ in range(COD_MAP_INSERT_RETRIES):
        id_registro: int | None = None
        try:
            with dal.transaction():
                alocado = _alocar_proximo_codigo_mapa(dal, int(id_empresa))
                if isinstance(alocado, MapaError):
                    raise _AbortMapaTx(alocado)
                codigo_mapa, _seq = alocado

                cod_map = _gerar_proximo_cod_map(dal)
                if isinstance(cod_map, MapaError):
                    raise _AbortMapaTx(cod_map)

                ok_map = False
                try:
                    ok_map = dal.create(
                        """
                        INSERT INTO tb_map (
                            cod_map, codigo_mapa, id_usuario, id_responsavel, id_empresa, id_linha, id_turno,
                            data, inicio_jornada_des, fim_jornada_des, observacao
                        ) VALUES (?, ?, ?, ?, ?, NULL, ?, ?, ?, ?, ?)
                        """,
                        (
                            cod_map,
                            codigo_mapa,
                            id_usuario,
                            id_usuario,
                            int(id_empresa),
                            int(id_turno),
                            data_parsed.isoformat(),
                            inicio_sql,
                            fim_sql,
                            observacao,
                        ),
                    )
                except Exception:
                    ok_map = False
                if not ok_map:
                    ok_map = dal.create(
                        """
                        INSERT INTO tb_map (
                            cod_map, codigo_mapa, id_usuario, id_empresa, id_linha, id_turno,
                            data, inicio_jornada_des, fim_jornada_des, observacao
                        ) VALUES (?, ?, ?, ?, NULL, ?, ?, ?, ?, ?)
                        """,
                        (
                            cod_map,
                            codigo_mapa,
                            id_usuario,
                            int(id_empresa),
                            int(id_turno),
                            data_parsed.isoformat(),
                            inicio_sql,
                            fim_sql,
                            observacao,
                        ),
                    )
                if not ok_map:
                    raise _AbortMapaTx(
                        MapaError(
                            "Conflito ao gerar código do MAPA. Tente novamente.",
                            "cod_map_conflito",
                        )
                    )

                row = dal.read(
                    "SELECT id_registro FROM tb_map WHERE codigo_mapa = ?",
                    (codigo_mapa,),
                )
                if row.empty:
                    raise _AbortMapaTx(
                        MapaError("Falha ao criar MAPA.", "persistencia")
                    )
                id_registro = int(row.iloc[0]["id_registro"])
        except _AbortMapaTx as abort:
            if abort.erro.codigo == "cod_map_conflito":
                last_error = abort.erro
                try:
                    _assegurar_gerador_cod_map(dal, force_sync=True)
                except Exception:  # noqa: BLE001
                    logger.exception("Falha ao ressincronizar sequência de cod_map")
                continue
            return abort.erro
        except Exception as exc:  # noqa: BLE001
            if _is_unique_violation(exc):
                last_error = MapaError(
                    "Conflito ao gerar código do MAPA. Tente novamente.",
                    "cod_map_conflito",
                )
                try:
                    _assegurar_gerador_cod_map(dal, force_sync=True)
                except Exception:  # noqa: BLE001
                    logger.exception("Falha ao ressincronizar sequência de cod_map")
                continue
            msg_l = str(exc).lower()
            # Conexão/transação inconsistente (ex.: set_session) — tenta de novo.
            if "set_session" in msg_l or "in a transaction" in msg_l:
                last_error = MapaError(
                    "Falha ao criar MAPA. Tente novamente.",
                    "persistencia",
                )
                continue
            logger.exception("Falha inesperada ao criar MAPA")
            return MapaError(
                "Falha ao criar MAPA. Tente novamente.",
                "persistencia",
            )

        if id_registro is None:
            last_error = MapaError("Falha ao criar MAPA.", "persistencia")
            continue
        completo = obter_mapa_completo(dal, id_registro)
        if isinstance(completo, MapaError):
            return completo
        return completo

    return last_error or MapaError("Falha ao criar MAPA.", "persistencia")


def atualizar_mapa(
    dal, id_registro: int, payload: dict[str, Any]
) -> dict[str, Any] | MapaError:
    existe = dal.read(
        """
        SELECT id_registro, id_empresa, codigo_mapa
        FROM tb_map WHERE id_registro = ?
        """,
        (id_registro,),
    )
    if existe.empty:
        return MapaError("MAPA não encontrado.", "nao_encontrado")

    id_turno = _resolver_id_turno(dal, payload)
    if isinstance(id_turno, MapaError):
        return id_turno

    data_parsed = _parse_date(payload.get("data"))
    if isinstance(data_parsed, MapaError):
        return data_parsed

    inicio = _parse_hora_plantao(payload.get("inicio_jornada_des"), obrigatorio=True)
    fim = _parse_hora_plantao(payload.get("fim_jornada_des"), obrigatorio=True)
    if isinstance(inicio, MapaError):
        return inicio
    if isinstance(fim, MapaError):
        return fim
    assert isinstance(inicio, time) and isinstance(fim, time)
    err_plantao = _validar_plantao(inicio, fim)
    if err_plantao is not None:
        return err_plantao

    observacao = payload.get("observacao")
    inicio_sql = _hora_plantao_sql(inicio, data_parsed, dal)
    fim_sql = _hora_plantao_sql(fim, data_parsed, dal)

    ok = dal.update(
        """
        UPDATE tb_map
        SET id_turno = ?, data = ?,
            inicio_jornada_des = ?, fim_jornada_des = ?, observacao = ?
        WHERE id_registro = ?
        """,
        (
            int(id_turno),
            data_parsed.isoformat(),
            inicio_sql,
            fim_sql,
            observacao,
            id_registro,
        ),
    )
    if not ok:
        return MapaError("Falha ao atualizar MAPA.", "persistencia")

    # Legado: se ainda não tem empresa/código, permite vincular empresa uma vez.
    codigo_atual = _limpar_codigo_mapa(existe.iloc[0].get("codigo_mapa"))
    id_emp_atual = existe.iloc[0].get("id_empresa")
    sem_empresa = id_emp_atual is None or str(id_emp_atual).strip() in (
        "",
        "None",
        "nan",
    )
    if not codigo_atual and sem_empresa:
        raw_emp = payload.get("id_empresa")
        if raw_emp is not None and str(raw_emp).strip() not in ("", "null", "None"):
            try:
                id_emp = int(raw_emp)
            except (TypeError, ValueError):
                return MapaError("Empresa inválida.", "empresa_invalida")
            emp = dal.read(
                "SELECT id_empresa FROM tb_empresa WHERE id_empresa = ? AND ativo = 1",
                (id_emp,),
            )
            if emp.empty:
                return MapaError(
                    "Empresa não encontrada ou inativa.", "empresa_invalida"
                )
            try:
                with dal.transaction():
                    alocado = _alocar_proximo_codigo_mapa(dal, int(id_emp))
                    if isinstance(alocado, MapaError):
                        raise _AbortMapaTx(alocado)
                    codigo, _seq = alocado
                    ok_cod = dal.update(
                        """
                        UPDATE tb_map
                        SET id_empresa = ?, codigo_mapa = ?
                        WHERE id_registro = ?
                          AND id_empresa IS NULL
                          AND (codigo_mapa IS NULL OR TRIM(codigo_mapa) = '')
                        """,
                        (int(id_emp), codigo, int(id_registro)),
                    )
                    if not ok_cod:
                        raise _AbortMapaTx(
                            MapaError(
                                "Não foi possível atribuir o código do MAPA.",
                                "persistencia",
                            )
                        )
            except _AbortMapaTx as abort:
                return abort.erro

    completo = obter_mapa_completo(dal, id_registro)
    if isinstance(completo, MapaError):
        return completo
    return completo


def excluir_mapa(dal, id_registro: int) -> MapaError | None:
    itens = dal.read(
        "SELECT id_item FROM tb_item_map WHERE idmap = ?",
        (id_registro,),
    )
    for _, row in itens.iterrows():
        id_item = int(row["id_item"])
        dal.delete(
            "DELETE FROM tb_viagem WHERE id_item_registro = ?",
            (id_item,),
        )
    dal.delete("DELETE FROM tb_item_map WHERE idmap = ?", (id_registro,))
    ok = dal.delete("DELETE FROM tb_map WHERE id_registro = ?", (id_registro,))
    if not ok:
        return MapaError("MAPA não encontrado.", "nao_encontrado")
    return None


def excluir_todos_mapas(dal) -> dict[str, int] | MapaError:
    """Exclui todos os MAPAs (itens e viagens). Retorna quantidade removida."""
    df = dal.read("SELECT id_registro FROM tb_map ORDER BY id_registro")
    if df is None or df.empty:
        return {"excluidos": 0}

    total = int(len(df))

    def _bulk_delete() -> None:
        with dal.transaction():
            # Ordem: viagens → itens → mapas (respeita FKs)
            dal.delete(
                """
                DELETE FROM tb_viagem
                WHERE id_item_registro IN (SELECT id_item FROM tb_item_map)
                """
            )
            dal.delete("DELETE FROM tb_item_map")
            dal.delete("DELETE FROM tb_map")
            # Contadores por empresa voltam a 0 (próximo código = Prefixo01).
            dal.update("UPDATE tb_mapa_seq SET ultimo_seq = 0")

    try:
        _bulk_delete()
    except Exception as exc:  # noqa: BLE001
        msg = str(exc).lower()
        # Retry único se o pool entregou conexão com transação residual
        if "set_session" in msg or "in a transaction" in msg:
            try:
                _bulk_delete()
            except Exception:  # noqa: BLE001
                logger.exception("Falha ao excluir todos os MAPAs (retry)")
                return MapaError(
                    "Falha ao excluir os MAPAs. Tente novamente.",
                    "persistencia",
                )
        else:
            logger.exception("Falha ao excluir todos os MAPAs")
            return MapaError(
                "Falha ao excluir os MAPAs. Tente novamente.",
                "persistencia",
            )

    return {"excluidos": total}


def _resolver_id_veiculo(dal, payload: dict[str, Any]) -> int | MapaError:
    """Resolve veículo pela coluna numero_frota (prioritária) ou id_veiculo."""
    frota_raw = payload.get("numero_frota")
    if frota_raw is None or str(frota_raw).strip() == "":
        frota_raw = payload.get("carro")
    frota = str(frota_raw or "").strip()
    if frota:
        digits = "".join(ch for ch in frota if ch.isdigit())
        # Busca exclusivamente em tb_veiculo.numero_frota
        df = dal.read(
            """
            SELECT id_veiculo
            FROM tb_veiculo
            WHERE ativo = 1
              AND (
                    numero_frota = ?
                 OR TRIM(LEADING '0' FROM numero_frota) = TRIM(LEADING '0' FROM ?)
                 OR (CAST(numero_frota AS UNSIGNED) = CAST(? AS UNSIGNED) AND ? REGEXP '^[0-9]+$')
              )
            LIMIT 1
            """,
            (frota, digits or frota, digits or frota, digits or frota),
        )
        if df.empty:
            return MapaError("Carro não encontrado.", "validacao")
        return int(df.iloc[0]["id_veiculo"])

    id_veiculo = payload.get("id_veiculo")
    if id_veiculo is not None and str(id_veiculo).strip() != "":
        df = dal.read(
            """
            SELECT id_veiculo FROM tb_veiculo
            WHERE ativo = 1 AND id_veiculo = ?
            LIMIT 1
            """,
            (int(id_veiculo),),
        )
        if df.empty:
            return MapaError("Carro não encontrado.", "validacao")
        return int(df.iloc[0]["id_veiculo"])

    return MapaError("Carro é obrigatório.", "validacao")


def _resolver_id_motorista(dal, payload: dict[str, Any]) -> int | MapaError:
    """Resolve motorista exclusivamente pela coluna tb_motorista.matricula (ou id)."""
    mat_raw = payload.get("matricula")
    if mat_raw is None or str(mat_raw).strip() == "":
        mat_raw = payload.get("matricula_motorista")
    matricula = str(mat_raw or "").strip()
    if matricula:
        digits = "".join(ch for ch in matricula if ch.isdigit())
        # Busca apenas na coluna matricula (nunca em id_motorista / nome).
        df = dal.read(
            """
            SELECT id_motorista
            FROM tb_motorista
            WHERE ativo = 1
              AND (
                    matricula = ?
                 OR TRIM(LEADING '0' FROM matricula) = TRIM(LEADING '0' FROM ?)
                 OR (CAST(matricula AS UNSIGNED) = CAST(? AS UNSIGNED) AND ? REGEXP '^[0-9]+$')
              )
            LIMIT 1
            """,
            (matricula, digits or matricula, digits or matricula, digits or matricula),
        )
        if df.empty:
            return MapaError("Matrícula não encontrada.", "validacao")
        return int(df.iloc[0]["id_motorista"])

    id_motorista = payload.get("id_motorista")
    if id_motorista is not None and str(id_motorista).strip() != "":
        df = dal.read(
            """
            SELECT id_motorista FROM tb_motorista
            WHERE ativo = 1 AND id_motorista = ?
            LIMIT 1
            """,
            (int(id_motorista),),
        )
        if df.empty:
            return MapaError("Matrícula não encontrada.", "validacao")
        return int(df.iloc[0]["id_motorista"])

    return MapaError("Matrícula é obrigatória.", "validacao")


def _erro_veiculo_ja_alocado(
    dal,
    idmap: int,
    id_veiculo: int,
    id_item_excluir: int | None = None,
) -> MapaError | None:
    """
    Veículo em escala EM_ANDAMENTO (qualquer MAPA) bloqueia nova vinculação.
    idmap mantido na assinatura por compatibilidade com chamadas existentes.
    """
    del idmap  # ocupação é global por status
    params: list[Any] = [int(id_veiculo), STATUS_ESCALA_EM_ANDAMENTO]
    sql = """
        SELECT i.id_item, v.numero_frota, m.cod_map, m.codigo_mapa
        FROM tb_item_map i
        INNER JOIN tb_veiculo v ON v.id_veiculo = i.id_veiculo
        INNER JOIN tb_map m ON m.id_registro = i.idmap
        WHERE i.id_veiculo = ?
          AND UPPER(TRIM(i.status_escala)) = ?
    """
    if id_item_excluir is not None:
        sql += " AND i.id_item <> ?"
        params.append(int(id_item_excluir))
    sql += " LIMIT 1"
    existe = dal.read(sql, tuple(params))
    if existe.empty:
        return None
    frota = str(existe.iloc[0].get("numero_frota") or id_veiculo).strip().upper()
    num_map = _rotulo_mapa(
        existe.iloc[0].get("codigo_mapa"),
        existe.iloc[0].get("cod_map"),
    )
    return MapaError(
        f"O veículo {frota} está em operação no MAPA {num_map}. "
        "Dê baixa antes de vinculá-lo novamente.",
        "conflito_veiculo",
    )


def _erro_motorista_ja_alocado(
    dal,
    idmap: int,
    id_motorista: int,
    id_item_excluir: int | None = None,
) -> MapaError | None:
    """Motorista em escala EM_ANDAMENTO (qualquer MAPA) bloqueia nova vinculação."""
    del idmap
    params: list[Any] = [int(id_motorista), STATUS_ESCALA_EM_ANDAMENTO]
    sql = """
        SELECT i.id_item, mot.matricula, mot.nome, v.numero_frota
        FROM tb_item_map i
        INNER JOIN tb_motorista mot ON mot.id_motorista = i.id_motorista
        INNER JOIN tb_veiculo v ON v.id_veiculo = i.id_veiculo
        WHERE i.id_motorista = ?
          AND UPPER(TRIM(i.status_escala)) = ?
    """
    if id_item_excluir is not None:
        sql += " AND i.id_item <> ?"
        params.append(int(id_item_excluir))
    sql += " LIMIT 1"
    existe = dal.read(sql, tuple(params))
    if existe.empty:
        return None
    mat = str(existe.iloc[0].get("matricula") or "").strip()
    nome = str(existe.iloc[0].get("nome") or "").strip()
    rotulo = " — ".join(p for p in (mat, nome) if p) or str(id_motorista)
    frota = str(existe.iloc[0].get("numero_frota") or "").strip().upper() or "—"
    return MapaError(
        f"O motorista {rotulo} está em operação no veículo {frota}. "
        "Dê baixa antes de vinculá-lo novamente.",
        "conflito_motorista",
    )


def listar_ocupacao_escalas(
    dal, filtros: dict[str, Any] | None = None
) -> dict[str, list[dict[str, Any]]]:
    """
    Veículos e motoristas em escalas EM_ANDAMENTO.
    Filtros opcionais: id_mapa, id_empresa, id_linha, data.
    """
    filtros = dict(filtros or {})
    where = ["UPPER(TRIM(i.status_escala)) = ?"]
    params: list[Any] = [STATUS_ESCALA_EM_ANDAMENTO]

    id_mapa = filtros.get("id_mapa")
    if id_mapa not in (None, ""):
        where.append("i.idmap = ?")
        params.append(int(id_mapa))

    id_empresa = filtros.get("id_empresa")
    if id_empresa not in (None, ""):
        where.append("l.id_empresa = ?")
        params.append(int(id_empresa))

    id_linha = filtros.get("id_linha")
    if id_linha not in (None, ""):
        where.append("i.id_linha = ?")
        params.append(int(id_linha))

    data_ref = filtros.get("data")
    if data_ref not in (None, ""):
        data_ok = _parse_date(data_ref)
        if not isinstance(data_ok, MapaError):
            where.append("m.data = ?")
            params.append(data_ok.strftime("%Y-%m-%d"))

    where_sql = " AND ".join(where)
    df = dal.read(
        f"""
        SELECT i.id_item, i.idmap, i.id_veiculo, i.id_motorista, i.status_escala,
               i.inicio_real, i.chegada_ponto, i.hor_ini_jor,
               v.numero_frota,
               mot.matricula AS matricula_motorista, mot.nome AS nome_motorista,
               m.cod_map, m.codigo_mapa, m.data AS data_mapa
        FROM tb_item_map i
        INNER JOIN tb_veiculo v ON v.id_veiculo = i.id_veiculo
        INNER JOIN tb_map m ON m.id_registro = i.idmap
        INNER JOIN tb_linha l ON l.id_linha = i.id_linha
        LEFT JOIN tb_motorista mot ON mot.id_motorista = i.id_motorista
        WHERE {where_sql}
        ORDER BY v.numero_frota, i.id_item
        """,
        tuple(params),
    )

    veiculos_ocupados: list[dict[str, Any]] = []
    motoristas_ocupados: list[dict[str, Any]] = []
    if df.empty:
        return {
            "veiculos_ocupados": veiculos_ocupados,
            "motoristas_ocupados": motoristas_ocupados,
            # aliases legados (compatibilidade)
            "veiculos": veiculos_ocupados,
            "motoristas": motoristas_ocupados,
        }

    for _, row in df.iterrows():
        inicio_dt = (
            _as_datetime(row.get("inicio_real"))
            or _as_datetime(row.get("chegada_ponto"))
            or _as_datetime(row.get("hor_ini_jor"))
        )
        inicio_hhmm = _format_hhmm(inicio_dt) if inicio_dt else None
        prefixo = str(row.get("numero_frota") or "").strip().upper()
        status = (
            str(row.get("status_escala") or STATUS_ESCALA_EM_ANDAMENTO)
            .strip()
            .upper()
            or STATUS_ESCALA_EM_ANDAMENTO
        )
        id_item = int(row["id_item"])
        id_mapa_val = int(row["idmap"])
        id_veiculo = int(row["id_veiculo"])
        id_mot_raw = row.get("id_motorista")
        id_motorista = None
        try:
            if id_mot_raw is not None and str(id_mot_raw).strip() not in (
                "",
                "None",
                "nan",
            ):
                id_motorista = int(id_mot_raw)
        except (TypeError, ValueError):
            id_motorista = None

        mat = str(row.get("matricula_motorista") or "").strip() or None
        nome = str(row.get("nome_motorista") or "").strip() or None

        veiculos_ocupados.append(
            {
                "id_veiculo": id_veiculo,
                "prefixo": prefixo,
                "numero_frota": prefixo,
                "id_mapa_item": id_item,
                "id_item": id_item,
                "id_mapa": id_mapa_val,
                "idmap": id_mapa_val,
                "cod_map": int(row["cod_map"]) if row.get("cod_map") is not None else None,
                "codigo_mapa": (
                    str(row["codigo_mapa"]).strip()
                    if row.get("codigo_mapa") is not None
                    and str(row.get("codigo_mapa")).strip()
                    else None
                ),
                "id_motorista": id_motorista,
                "matricula_motorista": mat,
                "nome_motorista": nome,
                "inicio_real": inicio_hhmm,
                "status": status,
                "status_escala": status,
            }
        )
        if id_motorista is not None:
            motoristas_ocupados.append(
                {
                    "id_motorista": id_motorista,
                    "matricula": mat,
                    "nome": nome,
                    "id_mapa_item": id_item,
                    "id_item": id_item,
                    "id_mapa": id_mapa_val,
                    "idmap": id_mapa_val,
                    "cod_map": int(row["cod_map"]) if row.get("cod_map") is not None else None,
                    "codigo_mapa": (
                        str(row["codigo_mapa"]).strip()
                        if row.get("codigo_mapa") is not None
                        and str(row.get("codigo_mapa")).strip()
                        else None
                    ),
                    "id_veiculo": id_veiculo,
                    "prefixo_veiculo": prefixo,
                    "numero_frota": prefixo,
                    "inicio_real": inicio_hhmm,
                    "status": status,
                    "status_escala": status,
                }
            )

    return {
        "veiculos_ocupados": veiculos_ocupados,
        "motoristas_ocupados": motoristas_ocupados,
        "veiculos": veiculos_ocupados,
        "motoristas": motoristas_ocupados,
    }


def _as_datetime(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.replace(tzinfo=None) if getattr(value, "tzinfo", None) else value
    # pandas.Timestamp / tipos com to_pydatetime
    to_py = getattr(value, "to_pydatetime", None)
    if callable(to_py):
        try:
            dt = to_py()
            if isinstance(dt, datetime):
                return dt.replace(tzinfo=None) if dt.tzinfo else dt
        except Exception:
            pass
    texto = str(value).strip()
    if not texto or texto.lower() in ("none", "null", "nat", "nan"):
        return None
    texto = texto.replace("T", " ")
    texto = re.sub(r"\s*(GMT|UTC|Z)$", "", texto, flags=re.IGNORECASE).strip()
    texto = re.sub(r"([+-]\d{2}:?\d{2})$", "", texto).strip()
    candidatos = [texto]
    if len(texto) >= 19:
        candidatos.insert(0, texto[:19])
    elif len(texto) == 16:
        candidatos.insert(0, texto + ":00")
    for candidato in candidatos:
        for fmt in (
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M",
            "%d/%m/%Y %H:%M:%S",
            "%d/%m/%Y %H:%M",
            "%H:%M:%S",
            "%H:%M",
        ):
            try:
                dt = datetime.strptime(candidato, fmt)
                if fmt in ("%H:%M:%S", "%H:%M"):
                    # Sem data: sentinela para combinar com data do MAPA depois
                    return datetime(1900, 1, 1, dt.hour, dt.minute, dt.second)
                return dt
            except ValueError:
                continue
    return None


def _combinar_com_data_mapa(dt: datetime | None, data_mapa: Any) -> datetime | None:
    """Se dt veio só com hora (data 1900-01-01), aplica a data do MAPA."""
    if dt is None:
        return None
    if dt.year != 1900 or dt.month != 1 or dt.day != 1:
        return dt
    base = _coerce_mapa_date(data_mapa)
    if base is None:
        return None
    return datetime(base.year, base.month, base.day, dt.hour, dt.minute, dt.second)


def _format_hhmm(dt: datetime) -> str:
    return dt.strftime("%H:%M")


def _duracao_minutos(inicio: datetime, fim: datetime) -> int:
    """Minutos trabalhados (fim - inicio); suporta cruzamento de meia-noite."""
    delta = fim - inicio
    return int(delta.total_seconds() // 60)


def _format_hhmm_from_minutos(minutos: int) -> str:
    m = max(0, int(minutos))
    h, mm = divmod(m, 60)
    return f"{h:02d}:{mm:02d}"


def _format_hhmm_signed(minutos: int) -> str:
    sign = "-" if minutos < 0 else "+"
    return f"{sign}{_format_hhmm_from_minutos(abs(int(minutos)))}"


def _hhmm_str(value: Any) -> str | None:
    dt = _as_datetime(value)
    if dt is None:
        texto = str(value or "").strip()
        m = re.search(r"(\d{2}):(\d{2})", texto)
        return f"{m.group(1)}:{m.group(2)}" if m else (texto or None)
    return dt.strftime("%H:%M")


def _intervalos_sobrepoem(
    a0: datetime, a1: datetime | None, b0: datetime, b1: datetime | None
) -> bool:
    """
    Sobreposição com extremos abertos à direita: [a0, a1) e [b0, b1).
    a1/b1 None = intervalo aberto (em andamento).
    Limite igual (a1 == b0) NÃO sobrepõe — permite troca no mesmo instante.
    """
    fim_a = a1 if a1 is not None else datetime.max
    fim_b = b1 if b1 is not None else datetime.max
    return a0 < fim_b and b0 < fim_a


def _resolver_inicio_real_item(
    payload: dict[str, Any],
    chegada: datetime | None,
    hor_ini: datetime | None,
) -> datetime:
    raw = payload.get("inicio_real", payload.get("inicio_real_jornada"))
    parsed = _as_datetime(raw) if raw is not None else None
    if parsed is not None:
        return parsed
    if chegada is not None:
        return chegada
    if hor_ini is not None:
        return hor_ini
    return datetime.now().replace(second=0, microsecond=0)


def _erro_sobreposicao_motorista(
    dal,
    id_motorista: int,
    inicio: datetime,
    fim: datetime | None,
    id_item_excluir: int | None = None,
) -> MapaError | None:
    """Bloqueia sobreposição de intervalos reais (ou planejados se real ausente)."""
    rows = dal.read(
        """
        SELECT id_item, inicio_real, fim_real, hor_ini_jor, hor_fim_jor,
               chegada_ponto, status_escala
        FROM tb_item_map
        WHERE id_motorista = ?
        """,
        (int(id_motorista),),
    )
    if rows.empty:
        return None
    for _, row in rows.iterrows():
        id_outro = int(row["id_item"])
        if id_item_excluir is not None and id_outro == int(id_item_excluir):
            continue
        ini = (
            _as_datetime(row.get("inicio_real"))
            or _as_datetime(row.get("chegada_ponto"))
            or _as_datetime(row.get("hor_ini_jor"))
        )
        if ini is None:
            continue
        status = str(row.get("status_escala") or "").strip().upper()
        fim_o = _as_datetime(row.get("fim_real"))
        if fim_o is None and status == STATUS_ESCALA_ENCERRADA:
            fim_o = _as_datetime(row.get("baixa_em")) or _as_datetime(row.get("hor_fim_jor"))
        if fim_o is None and status != STATUS_ESCALA_ENCERRADA:
            fim_o = None  # em andamento
        elif fim_o is None:
            fim_o = _as_datetime(row.get("hor_fim_jor"))
        if _intervalos_sobrepoem(inicio, fim, ini, fim_o):
            return MapaError(
                "Intervalo sobrepõe outra escala do mesmo motorista. "
                "Ajuste o início/fim real ou dê baixa na escala anterior.",
                "conflito_sobreposicao",
            )
    return None


def _ultima_chegada_viagem(
    dal, id_item: int, id_viagem_excluir: int | None = None, data_mapa: Any = None
) -> datetime | None:
    params: list[Any] = [int(id_item)]
    sql = """
        SELECT horario_saida, horario_chegada
        FROM tb_viagem
        WHERE id_item_registro = ?
    """
    if id_viagem_excluir is not None:
        sql += " AND id_viagem <> ?"
        params.append(int(id_viagem_excluir))
    df = dal.read(sql, tuple(params))
    if df.empty:
        return None
    ultima: datetime | None = None
    for _, row in df.iterrows():
        cheg = _combinar_com_data_mapa(
            _as_datetime(row.get("horario_chegada")), data_mapa
        )
        if cheg is None:
            continue
        if ultima is None or cheg > ultima:
            ultima = cheg
    return ultima


def _frota_do_item(dal, id_item: int) -> str:
    df = dal.read(
        """
        SELECT v.numero_frota
        FROM tb_item_map i
        INNER JOIN tb_veiculo v ON v.id_veiculo = i.id_veiculo
        WHERE i.id_item = ?
        LIMIT 1
        """,
        (int(id_item),),
    )
    if df.empty:
        return str(id_item)
    return str(df.iloc[0].get("numero_frota") or id_item).strip().upper()


def _data_mapa_do_item(dal, id_item: int) -> Any:
    df = dal.read(
        """
        SELECT m.data AS data_mapa
        FROM tb_item_map i
        INNER JOIN tb_map m ON m.id_registro = i.idmap
        WHERE i.id_item = ?
        LIMIT 1
        """,
        (int(id_item),),
    )
    if df.empty:
        return None
    return df.iloc[0].get("data_mapa")


def _janela_ativa_escala(dal, id_item: int) -> tuple[datetime | None, datetime | None]:
    """Horários ativos da escala (início real/planejado → fim planejado/real)."""
    df = dal.read(
        """
        SELECT inicio_real, chegada_ponto, hor_ini_jor, hor_fim_jor, fim_real, baixa_em
        FROM tb_item_map
        WHERE id_item = ?
        LIMIT 1
        """,
        (int(id_item),),
    )
    if df.empty:
        return None, None
    row = df.iloc[0]
    data_mapa = _data_mapa_do_item(dal, id_item)
    inicio = _combinar_com_data_mapa(
        _as_datetime(row.get("inicio_real"))
        or _as_datetime(row.get("chegada_ponto"))
        or _as_datetime(row.get("hor_ini_jor")),
        data_mapa,
    )
    fim = _combinar_com_data_mapa(
        _as_datetime(row.get("fim_real"))
        or _as_datetime(row.get("baixa_em"))
        or _as_datetime(row.get("hor_fim_jor")),
        data_mapa,
    )
    return inicio, fim


def _viagens_sobrepoem(
    nova_saida: datetime,
    nova_chegada: datetime,
    saida_existente: datetime,
    chegada_existente: datetime,
) -> bool:
    """
    Conflito quando há interseção:
    nova_saida < chegada_existente AND nova_chegada > saida_existente.
    Limite igual (nova_saida == chegada_existente) NÃO conflita.
    """
    return nova_saida < chegada_existente and nova_chegada > saida_existente


def _erro_conflito_horarios_viagem(
    dal,
    id_item: int,
    saida: datetime,
    chegada: datetime,
    id_viagem_excluir: int | None = None,
) -> MapaError | None:
    """
    Percurso sequencial na mesma escala (mesmo id_mapa_item):
    - chegada > saida (senão 422);
    - sem interseção com qualquer viagem do item;
    - na criação, saída >= chegada da última viagem;
    - dentro da janela ativa da escala (jornada), quando definida.
    """
    if chegada <= saida:
        return MapaError(
            "A chegada deve ser posterior à saída da viagem.",
            "horario_invalido",
        )

    data_mapa = _data_mapa_do_item(dal, id_item)
    saida_n = _combinar_com_data_mapa(saida, data_mapa) or saida
    chegada_n = _combinar_com_data_mapa(chegada, data_mapa) or chegada
    if chegada_n <= saida_n:
        return MapaError(
            "A chegada deve ser posterior à saída da viagem.",
            "horario_invalido",
        )

    frota = _frota_do_item(dal, id_item)

    inicio_esc, fim_esc = _janela_ativa_escala(dal, id_item)
    if inicio_esc is not None and saida_n < inicio_esc:
        return MapaError(
            "A viagem não pode começar antes do início ativo da escala "
            f"({_format_hhmm(inicio_esc)}).",
            "conflito_horario",
        )
    if fim_esc is not None and chegada_n > fim_esc:
        return MapaError(
            "A viagem não pode terminar após o fim da jornada da escala "
            f"({_format_hhmm(fim_esc)}).",
            "conflito_horario",
        )

    params: list[Any] = [int(id_item)]
    sql = """
        SELECT id_viagem, horario_saida, horario_chegada
        FROM tb_viagem
        WHERE id_item_registro = ?
    """
    if id_viagem_excluir is not None:
        sql += " AND id_viagem <> ?"
        params.append(int(id_viagem_excluir))
    existentes = dal.read(sql, tuple(params))

    ultima_chegada: datetime | None = None
    ultima_saida: datetime | None = None
    for _, row in existentes.iterrows():
        v0 = _combinar_com_data_mapa(_as_datetime(row.get("horario_saida")), data_mapa)
        v1 = _combinar_com_data_mapa(
            _as_datetime(row.get("horario_chegada")), data_mapa
        )
        if v0 is None or v1 is None:
            continue
        if _viagens_sobrepoem(saida_n, chegada_n, v0, v1):
            return MapaError(
                f"O veículo {frota} já possui viagem entre {_format_hhmm(v0)} e "
                f"{_format_hhmm(v1)}. Informe uma saída a partir de {_format_hhmm(v1)}.",
                "conflito_horario",
            )
        if ultima_chegada is None or v1 > ultima_chegada:
            ultima_chegada = v1
            ultima_saida = v0

    # Criação: próxima saída somente a partir da última chegada
    if id_viagem_excluir is None and ultima_chegada is not None and saida_n < ultima_chegada:
        saida_ref = ultima_saida or ultima_chegada
        return MapaError(
            f"O veículo {frota} já possui viagem entre {_format_hhmm(saida_ref)} e "
            f"{_format_hhmm(ultima_chegada)}. Informe uma saída a partir de "
            f"{_format_hhmm(ultima_chegada)}.",
            "conflito_horario",
        )
    return None


def _enriquecer_campos_horas_item(item: dict[str, Any]) -> dict[str, Any]:
    """Aliases de leitura: planejado + reais + duração formatada."""
    item["inicio_jornada_planejado"] = item.get("hor_ini_jor")
    item["fim_jornada_planejado"] = item.get("hor_fim_jor")
    if item.get("fim_real") in (None, "") and item.get("baixa_em") not in (None, ""):
        item["fim_real"] = item.get("baixa_em")
    dur = item.get("duracao_trabalhada_minutos")
    try:
        if dur is not None and str(dur).strip() != "":
            item["duracao_trabalhada_hhmm"] = _format_hhmm_from_minutos(int(dur))
        else:
            item["duracao_trabalhada_hhmm"] = None
    except (TypeError, ValueError):
        item["duracao_trabalhada_hhmm"] = None
    return item


def dar_baixa_item_map(
    dal, id_item: int, payload: dict[str, Any] | None = None
) -> dict[str, Any] | MapaError:
    """
    Encerra a escala com fim real e duração trabalhadas.
    Não apaga histórico/viagens; libera veículo/motorista.
    """
    body = dict(payload or {})
    atual = dal.read(
        """
        SELECT id_item, id_motorista, id_veiculo, status_escala,
               inicio_real, chegada_ponto, hor_ini_jor, fim_real, baixa_em
        FROM tb_item_map WHERE id_item = ? LIMIT 1
        """,
        (int(id_item),),
    )
    if atual.empty:
        return MapaError("Item não encontrado.", "nao_encontrado")

    row = atual.iloc[0]
    status = str(row.get("status_escala") or "").strip().upper()
    if status == STATUS_ESCALA_ENCERRADA:
        return MapaError("Esta escala já está encerrada.", "validacao")
    if status and status != STATUS_ESCALA_EM_ANDAMENTO:
        return MapaError(
            "Somente escalas em andamento podem receber baixa.",
            "validacao",
        )

    inicio = (
        _as_datetime(row.get("inicio_real"))
        or _as_datetime(row.get("chegada_ponto"))
        or _as_datetime(row.get("hor_ini_jor"))
    )
    if inicio is None:
        return MapaError(
            "Escala sem início real. Informe o início antes de dar baixa.",
            "validacao",
        )

    fim_raw = body.get("fim_real", body.get("data_hora_baixa", body.get("baixa_em")))
    if fim_raw is None or str(fim_raw).strip() == "":
        return MapaError(
            "Informe a data/hora real de encerramento (fim_real).",
            "validacao",
        )
    fim = _as_datetime(fim_raw)
    if fim is None:
        return MapaError("Data/hora de encerramento inválida.", "validacao")
    if fim < inicio:
        return MapaError(
            "O fim real não pode ser anterior ao início real.",
            "validacao",
        )

    ultima_viagem = _ultima_chegada_viagem(
        dal, int(id_item), data_mapa=_data_mapa_do_item(dal, int(id_item))
    )
    if ultima_viagem is not None and fim < ultima_viagem:
        return MapaError(
            "Não é possível dar baixa antes do fim da última viagem registrada "
            f"({ultima_viagem.strftime('%H:%M')}).",
            "validacao",
        )

    minutos = _duracao_minutos(inicio, fim)
    if minutos < 0:
        return MapaError("Duração trabalhadas inválida.", "validacao")

    motivo = str(body.get("motivo_baixa") or "").strip() or None
    if motivo and len(motivo) > 120:
        return MapaError("motivo_baixa excede 120 caracteres.", "validacao")
    obs = str(body.get("observacao_baixa") or "").strip() or None
    if obs and len(obs) > 500:
        return MapaError("observacao_baixa excede 500 caracteres.", "validacao")

    fim_txt = fim.strftime("%Y-%m-%d %H:%M:%S")
    inicio_txt = inicio.strftime("%Y-%m-%d %H:%M:%S")
    data_baixa_txt = fim.strftime("%Y-%m-%d")
    hora_baixa_txt = fim.strftime("%H:%M:%S")

    with dal.transaction():
        ok = dal.update(
            """
            UPDATE tb_item_map
            SET status_escala = ?,
                inicio_real = COALESCE(inicio_real, ?),
                fim_real = ?,
                baixa_em = ?,
                data_baixa = ?,
                hora_baixa = ?,
                motivo_baixa = ?,
                observacao_baixa = ?,
                duracao_trabalhada_minutos = ?
            WHERE id_item = ?
              AND UPPER(TRIM(status_escala)) = ?
            """,
            (
                STATUS_ESCALA_ENCERRADA,
                inicio_txt,
                fim_txt,
                fim_txt,
                data_baixa_txt,
                hora_baixa_txt,
                motivo,
                obs,
                minutos,
                int(id_item),
                STATUS_ESCALA_EM_ANDAMENTO,
            ),
        )
        if not ok:
            return MapaError(
                "Não foi possível dar baixa (escala já encerrada ou alterada).",
                "conflito_baixa",
            )
        confere = dal.read(
            """
            SELECT id_item, status_escala, fim_real, duracao_trabalhada_minutos
            FROM tb_item_map WHERE id_item = ? LIMIT 1
            """,
            (int(id_item),),
        )
        if confere.empty:
            return MapaError("Item não encontrado.", "nao_encontrado")
        st = str(confere.iloc[0].get("status_escala") or "").strip().upper()
        if st != STATUS_ESCALA_ENCERRADA:
            return MapaError(
                "Não foi possível dar baixa (conflito concorrente).",
                "conflito_baixa",
            )

    item = _item_map_detalhe(dal, int(id_item))
    if item is None:
        return MapaError("Item não encontrado.", "nao_encontrado")
    return item


def obter_banco_horas_motorista(
    dal,
    id_motorista: int,
    data_ref: date,
    *,
    id_empresa: int | None = None,
    id_linha: int | None = None,
    situacao: str | None = None,
) -> dict[str, Any] | MapaError:
    """
    Controle operacional do dia: períodos por veículo + totais.
    Não é integração de folha/RH.
    """
    mot = dal.read(
        """
        SELECT id_motorista, matricula, nome, ativo
        FROM tb_motorista WHERE id_motorista = ? LIMIT 1
        """,
        (int(id_motorista),),
    )
    if mot.empty:
        return MapaError("Motorista não encontrado.", "nao_encontrado")

    dia = data_ref.strftime("%Y-%m-%d")
    # Escalas cujo início real (ou planejado) cai no dia, ou atravessam o dia
    itens_df = dal.read(
        """
        SELECT i.*,
               v.numero_frota,
               m.data AS data_mapa,
               m.id_empresa,
               m.id_linha AS id_linha_mapa,
               e.descricao AS empresa_descricao,
               l.codigo_linha,
               l.descricao AS linha_descricao,
               u.nome AS responsavel_registro,
               u.matricula AS matricula_responsavel
        FROM tb_item_map i
        INNER JOIN tb_veiculo v ON v.id_veiculo = i.id_veiculo
        INNER JOIN tb_map m ON m.id_registro = i.idmap
        LEFT JOIN tb_empresa e ON e.id_empresa = m.id_empresa
        LEFT JOIN tb_linha l ON l.id_linha = COALESCE(i.id_linha, m.id_linha)
        LEFT JOIN tb_usuario u ON u.id_usuario = m.id_usuario
        WHERE i.id_motorista = ?
        ORDER BY i.id_item
        """,
        (int(id_motorista),),
    )

    agora = _agora_operacional()
    # Agrupamento operacional: data de início do MAPA (m.data), não só calendário do início_real
    dia_ini = datetime.combine(data_ref, datetime.min.time())
    dia_fim = datetime.combine(data_ref, datetime.max.time().replace(microsecond=0))

    encerradas: list[dict[str, Any]] = []
    em_andamento: dict[str, Any] | None = None
    alertas: list[str] = []
    intervalos_fechados: list[tuple[datetime, datetime, int]] = []

    if not itens_df.empty:
        for _, row in itens_df.iterrows():
            item = row.to_dict()
            data_mapa = _coerce_mapa_date(item.get("data_mapa") or item.get("data"))
            # Preferência: data operacional = data de início do MAPA
            if data_mapa is not None and data_mapa != data_ref:
                continue
            ini = (
                _as_datetime(item.get("inicio_real"))
                or _as_datetime(item.get("chegada_ponto"))
                or _as_datetime(item.get("hor_ini_jor"))
            )
            if ini is None:
                continue
            status = str(item.get("status_escala") or "").strip().upper()
            fim = _as_datetime(item.get("fim_real")) or _as_datetime(item.get("baixa_em"))
            fim_ref = fim if fim is not None else agora
            if data_mapa is None:
                # Legado sem data_mapa: mantém filtro por intervalo no dia
                if not (ini < dia_fim and fim_ref >= dia_ini):
                    continue

            if id_empresa is not None:
                try:
                    if int(item.get("id_empresa") or -1) != int(id_empresa):
                        continue
                except (TypeError, ValueError):
                    continue
            if id_linha is not None:
                try:
                    lid = item.get("id_linha")
                    if lid is None:
                        lid = item.get("id_linha_mapa")
                    if int(lid or -1) != int(id_linha):
                        continue
                except (TypeError, ValueError):
                    continue

            situacao_norm = (situacao or "").strip().lower()
            if situacao_norm in ("encerrada", "em_andamento"):
                if situacao_norm == "encerrada" and status != STATUS_ESCALA_ENCERRADA:
                    continue
                if situacao_norm == "em_andamento" and status == STATUS_ESCALA_ENCERRADA:
                    continue

            frota = str(item.get("numero_frota") or item.get("id_veiculo") or "")
            previsto_ini = _as_datetime(item.get("hor_ini_jor"))
            previsto_fim = _as_datetime(item.get("hor_fim_jor"))
            # Viagens da escala — horários reais/planejados sem inventar chegada.
            viagens: list[dict[str, Any]] = []
            viagens_df = dal.read(
                """
                SELECT id_viagem, horario_saida, horario_chegada,
                       qtd_pas_ida, qtd_pas_volta, placa
                FROM tb_viagem
                WHERE id_item_registro = ?
                ORDER BY horario_saida ASC, id_viagem ASC
                """,
                (int(item["id_item"]),),
            )
            if viagens_df is not None and not getattr(viagens_df, "empty", True):
                for _, vr in viagens_df.iterrows():
                    vrow = vr.to_dict()
                    viagens.append(
                        {
                            "id_viagem": int(vrow["id_viagem"]),
                            "horario_saida": _hhmm_str(vrow.get("horario_saida")),
                            "horario_chegada": _hhmm_str(vrow.get("horario_chegada")),
                            "qtd_pas_ida": vrow.get("qtd_pas_ida"),
                            "qtd_pas_volta": vrow.get("qtd_pas_volta"),
                        }
                    )

            base = {
                "id_item": int(item["id_item"]),
                "idmap": int(item["idmap"]),
                "id_veiculo": int(item["id_veiculo"]),
                "numero_frota": frota,
                "id_empresa": int(item["id_empresa"]) if item.get("id_empresa") is not None else None,
                "empresa": item.get("empresa_descricao"),
                "id_linha": int(item["id_linha"]) if item.get("id_linha") is not None else None,
                "codigo_linha": item.get("codigo_linha"),
                "linha": item.get("linha_descricao") or item.get("codigo_linha"),
                "inicio_real": ini.strftime("%Y-%m-%d %H:%M:%S"),
                "jornada_prevista_ini": (
                    previsto_ini.strftime("%Y-%m-%d %H:%M:%S") if previsto_ini else None
                ),
                "jornada_prevista_fim": (
                    previsto_fim.strftime("%Y-%m-%d %H:%M:%S") if previsto_fim else None
                ),
                "responsavel_registro": item.get("responsavel_registro"),
                "matricula_responsavel": item.get("matricula_responsavel"),
                "viagens": viagens,
                "status_escala": status or STATUS_ESCALA_EM_ANDAMENTO,
            }

            if status == STATUS_ESCALA_ENCERRADA and fim is not None:
                dur = item.get("duracao_trabalhada_minutos")
                try:
                    minutos = int(dur) if dur is not None and str(dur).strip() != "" else _duracao_minutos(ini, fim)
                except (TypeError, ValueError):
                    minutos = _duracao_minutos(ini, fim)
                # Detecta sobreposição com já acumulados (legado)
                for a0, a1, _aid in intervalos_fechados:
                    if _intervalos_sobrepoem(ini, fim, a0, a1):
                        alertas.append(
                            f"Sobreposição detectada entre escalas (veículo {frota}). "
                            "Conferir dados legados — minutos não foram somados em duplicidade."
                        )
                        break
                else:
                    intervalos_fechados.append((ini, fim, int(item["id_item"])))
                # Soma sem duplicar: usa união simples via merge de intervalos
                saldo = None
                if previsto_ini and previsto_fim:
                    previsto_min = _duracao_minutos(previsto_ini, previsto_fim)
                    saldo = minutos - previsto_min
                base.update(
                    {
                        "fim_real": fim.strftime("%Y-%m-%d %H:%M:%S"),
                        "duracao_trabalhada_minutos": minutos,
                        "duracao_trabalhada_hhmm": _format_hhmm_from_minutos(minutos),
                        "saldo_diario_minutos": saldo,
                        "saldo_diario_hhmm": (
                            _format_hhmm_signed(saldo) if saldo is not None else None
                        ),
                        "situacao": "encerrada",
                    }
                )
                encerradas.append(base)
            elif status != STATUS_ESCALA_ENCERRADA:
                est = _duracao_minutos(ini, agora) if agora >= ini else 0
                base.update(
                    {
                        # Nunca preencher fim com fim previsto da escala.
                        "fim_real": None,
                        "duracao_estimada_minutos": est,
                        "duracao_estimada_hhmm": _format_hhmm_from_minutos(est),
                        "estimativa": True,
                        "saldo_diario_minutos": None,
                        "saldo_diario_hhmm": None,
                        "situacao": "em_andamento",
                    }
                )
                em_andamento = base

    # Total encerrado sem duplicar sobreposições (merge intervalos)
    intervalos_fechados.sort(key=lambda x: x[0])
    merged: list[tuple[datetime, datetime]] = []
    for a0, a1, _ in intervalos_fechados:
        if not merged or a0 >= merged[-1][1]:
            merged.append((a0, a1))
        else:
            # overlap legado: estende sem somar duas vezes
            prev0, prev1 = merged[-1]
            merged[-1] = (prev0, max(prev1, a1))
            if "Sobreposição" not in " ".join(alertas):
                alertas.append(
                    "Intervalos legados sobrepostos foram unidos no total do dia."
                )

    total_encerrado = sum(_duracao_minutos(a, b) for a, b in merged)
    total_estimado = (
        int(em_andamento["duracao_estimada_minutos"]) if em_andamento else 0
    )

    # Lacunas entre escalas encerradas (informativo)
    for i in range(1, len(merged)):
        gap = _duracao_minutos(merged[i - 1][1], merged[i][0])
        if gap > 0:
            alertas.append(
                f"Lacuna de {_format_hhmm_from_minutos(gap)} entre escalas encerradas."
            )

    motorista = mot.iloc[0].to_dict()
    situacao_dia = "sem_registro"
    if encerradas and em_andamento:
        situacao_dia = "mista"
    elif encerradas:
        situacao_dia = "encerrada"
    elif em_andamento:
        situacao_dia = "em_andamento"

    saldo_total = None
    for esc in encerradas:
        s = esc.get("saldo_diario_minutos")
        if s is None:
            continue
        saldo_total = (saldo_total or 0) + int(s)

    return {
        "controle": "operacional",
        "aviso": "Controle operacional — não é integração oficial de folha de pagamento. Chegadas nunca são geradas pelo fim previsto da escala.",
        "motorista": {
            "id_motorista": int(motorista["id_motorista"]),
            "matricula": motorista.get("matricula"),
            "nome": motorista.get("nome"),
        },
        "data": dia,
        "situacao": situacao_dia,
        "escalas_encerradas": encerradas,
        "escala_em_andamento": em_andamento,
        "total_minutos_encerrados": total_encerrado,
        "total_encerrado_hhmm": _format_hhmm_from_minutos(total_encerrado),
        "total_minutos_estimativa_andamento": total_estimado,
        "total_estimativa_andamento_hhmm": _format_hhmm_from_minutos(total_estimado),
        "saldo_diario_minutos": saldo_total,
        "saldo_diario_hhmm": (
            _format_hhmm_signed(saldo_total) if saldo_total is not None else None
        ),
        "alertas": alertas,
    }


def listar_banco_horas_periodo(
    dal,
    id_motorista: int,
    data_ini: date,
    data_fim: date,
    *,
    id_empresa: int | None = None,
    id_linha: int | None = None,
    situacao: str | None = None,
) -> dict[str, Any] | MapaError:
    """Histórico diário no período — um registro por dia com movimento."""
    if data_fim < data_ini:
        return MapaError("Período inválido: data fim anterior à data início.", "validacao")
    if (data_fim - data_ini).days > 62:
        return MapaError("Período máximo de 62 dias.", "validacao")

    dias: list[dict[str, Any]] = []
    cursor = data_ini
    while cursor <= data_fim:
        dia = obter_banco_horas_motorista(
            dal,
            id_motorista,
            cursor,
            id_empresa=id_empresa,
            id_linha=id_linha,
            situacao=situacao,
        )
        if isinstance(dia, MapaError):
            return dia
        if dia["escalas_encerradas"] or dia["escala_em_andamento"]:
            dias.append(dia)
        cursor += timedelta(days=1)

    mot = dias[0]["motorista"] if dias else None
    if mot is None:
        base = obter_banco_horas_motorista(dal, id_motorista, data_ini)
        if isinstance(base, MapaError):
            return base
        mot = base["motorista"]

    return {
        "controle": "operacional",
        "aviso": "Controle operacional — não é integração oficial de folha de pagamento.",
        "motorista": mot,
        "data_ini": data_ini.strftime("%Y-%m-%d"),
        "data_fim": data_fim.strftime("%Y-%m-%d"),
        "dias": dias,
    }


def _validar_veiculo_ativo(dal, id_veiculo: int) -> MapaError | None:
    """Carro ativo independente da empresa (empresa fica no Mapa/Linha/Guia)."""
    vei = dal.read(
        "SELECT id_veiculo, ativo, numero_frota FROM tb_veiculo WHERE id_veiculo = ?",
        (int(id_veiculo),),
    )
    if vei.empty:
        return MapaError("Veículo não encontrado.", "validacao")
    if int(vei.iloc[0].get("ativo") or 0) not in (1, True):
        return MapaError("Veículo está inativo.", "validacao")
    return None


def _resolver_id_linha_item(dal, payload: dict[str, Any]) -> int | MapaError:
    """Linha obrigatória no item (PK ativa)."""
    raw = payload.get("id_linha")
    if raw is None or str(raw).strip() == "":
        return MapaError("Linha é obrigatória.", "validacao")
    try:
        id_linha = int(raw)
    except (TypeError, ValueError):
        return MapaError("Linha inválida.", "validacao")
    df = dal.read(
        "SELECT id_linha, id_empresa FROM tb_linha WHERE id_linha = ? AND ativo = 1",
        (id_linha,),
    )
    if df.empty:
        return MapaError("Linha não encontrada.", "nao_encontrado")
    return int(df.iloc[0]["id_linha"])


def _exigir_horarios_item(
    payload: dict[str, Any], data_mapa: Any
) -> tuple[Any, Any, Any] | MapaError:
    """Início, fim e chegada obrigatórios no item."""
    for key, label in (
        ("hor_ini_jor", "Início de jornada"),
        ("hor_fim_jor", "Fim de jornada"),
        ("chegada_ponto", "Chegada no ponto"),
    ):
        raw = payload.get(key)
        if raw is None or str(raw).strip() == "":
            return MapaError(f"{label} é obrigatório.", "validacao")
    horarios = _normalizar_horarios_item(payload, data_mapa)
    if isinstance(horarios, MapaError):
        return horarios
    hor_ini, hor_fim, chegada = horarios
    if hor_ini is None or hor_fim is None or chegada is None:
        return MapaError(
            "Início, fim de jornada e chegada ao ponto são obrigatórios.",
            "validacao",
        )
    if hor_ini >= hor_fim:
        return MapaError("Início da jornada deve ser anterior ao fim.", "validacao")
    return hor_ini, hor_fim, chegada


def criar_item_map(
    dal, id_registro: int, payload: dict[str, Any]
) -> dict[str, Any] | MapaError:
    mapa = dal.read(
        "SELECT id_registro, data FROM tb_map WHERE id_registro = ?",
        (id_registro,),
    )
    if mapa.empty:
        return MapaError("MAPA não encontrado.", "nao_encontrado")

    id_linha = _resolver_id_linha_item(dal, payload)
    if isinstance(id_linha, MapaError):
        return id_linha

    id_veiculo = _resolver_id_veiculo(dal, payload)
    if isinstance(id_veiculo, MapaError):
        return id_veiculo

    err_vei = _validar_veiculo_ativo(dal, int(id_veiculo))
    if err_vei is not None:
        return err_vei

    id_motorista = _resolver_id_motorista(dal, payload)
    if isinstance(id_motorista, MapaError):
        return id_motorista

    data_mapa = mapa.iloc[0]["data"]
    horarios = _exigir_horarios_item(payload, data_mapa)
    if isinstance(horarios, MapaError):
        return horarios
    hor_ini, hor_fim, chegada = horarios
    inicio_real = _resolver_inicio_real_item(payload, chegada, hor_ini)

    try:
        with dal.transaction():
            conflito = _erro_veiculo_ja_alocado(dal, id_registro, int(id_veiculo))
            if conflito is not None:
                return conflito

            conflito_mot = _erro_motorista_ja_alocado(
                dal, id_registro, int(id_motorista)
            )
            if conflito_mot is not None:
                return conflito_mot

            sobre = _erro_sobreposicao_motorista(
                dal, int(id_motorista), inicio_real, None
            )
            if sobre is not None:
                return sobre

            ok = dal.create(
                """
                INSERT INTO tb_item_map (
                    idmap, id_linha, id_veiculo, id_motorista,
                    hor_ini_jor, hor_fim_jor, chegada_ponto,
                    inicio_real, fim_real, status_escala, baixa_em,
                    motivo_baixa, observacao_baixa, duracao_trabalhada_minutos
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, NULL, ?, NULL, NULL, NULL, NULL)
                """,
                (
                    id_registro,
                    int(id_linha),
                    int(id_veiculo),
                    int(id_motorista),
                    hor_ini,
                    hor_fim,
                    chegada,
                    inicio_real.strftime("%Y-%m-%d %H:%M:%S"),
                    STATUS_ESCALA_EM_ANDAMENTO,
                ),
            )
            if not ok:
                conflito = _erro_veiculo_ja_alocado(
                    dal, id_registro, int(id_veiculo)
                )
                if conflito is not None:
                    return conflito
                conflito_mot = _erro_motorista_ja_alocado(
                    dal, id_registro, int(id_motorista)
                )
                if conflito_mot is not None:
                    return conflito_mot
                return MapaError(
                    "Falha ao gravar o registro no banco (verifique horários e vínculos).",
                    "persistencia",
                )

            row = dal.read(
                "SELECT MAX(id_item) AS id_item FROM tb_item_map WHERE idmap = ?",
                (id_registro,),
            )
            id_item = int(row.iloc[0]["id_item"])
    except Exception:
        return MapaError(
            "Falha ao gravar o registro no banco (verifique horários e vínculos).",
            "persistencia",
        )

    item = _item_map_detalhe(dal, id_item)
    if item is None:
        return MapaError("Item não encontrado.", "nao_encontrado")
    return item


def atualizar_item_map(
    dal, id_item: int, payload: dict[str, Any]
) -> dict[str, Any] | MapaError:
    atual = dal.read(
        """
        SELECT i.id_item, i.idmap, i.status_escala, i.id_veiculo, i.id_motorista,
               m.data AS data_mapa
        FROM tb_item_map i
        INNER JOIN tb_map m ON m.id_registro = i.idmap
        WHERE i.id_item = ?
        """,
        (id_item,),
    )
    if atual.empty:
        return MapaError("Item não encontrado.", "nao_encontrado")

    status = str(atual.iloc[0].get("status_escala") or "").strip().upper()
    if status == STATUS_ESCALA_ENCERRADA:
        return MapaError(
            "Esta escala foi encerrada e não pode ser alterada.",
            "validacao",
        )

    idmap = int(atual.iloc[0]["idmap"])
    id_veiculo_atual = int(atual.iloc[0]["id_veiculo"])
    id_mot_atual = (
        int(atual.iloc[0]["id_motorista"])
        if atual.iloc[0].get("id_motorista") is not None
        else None
    )

    id_linha = _resolver_id_linha_item(dal, payload)
    if isinstance(id_linha, MapaError):
        return id_linha

    id_veiculo = _resolver_id_veiculo(dal, payload)
    if isinstance(id_veiculo, MapaError):
        return id_veiculo

    err_vei = _validar_veiculo_ativo(dal, int(id_veiculo))
    if err_vei is not None:
        return err_vei

    id_motorista = _resolver_id_motorista(dal, payload)
    if isinstance(id_motorista, MapaError):
        return id_motorista

    # Após viagem/baixa/histórico: bloqueia troca direta de veículo/motorista
    viagens = dal.read(
        "SELECT COUNT(*) AS n FROM tb_viagem WHERE id_item_registro = ?",
        (int(id_item),),
    )
    n_viagens = int(viagens.iloc[0]["n"]) if not viagens.empty else 0
    muda_veiculo = int(id_veiculo) != id_veiculo_atual
    muda_motorista = id_mot_atual is not None and int(id_motorista) != id_mot_atual
    if n_viagens > 0 and (muda_veiculo or muda_motorista):
        return MapaError(
            "Após existir viagem nesta escala, não é permitido alterar veículo ou "
            "motorista no fluxo normal. Dê baixa e crie nova escala, ou use "
            "correção excepcional (Administrador).",
            "correcao_excepcional_requerida",
        )

    horarios = _exigir_horarios_item(payload, atual.iloc[0]["data_mapa"])
    if isinstance(horarios, MapaError):
        return horarios
    hor_ini, hor_fim, chegada = horarios
    inicio_real = _resolver_inicio_real_item(payload, chegada, hor_ini)

    try:
        with dal.transaction():
            conflito = _erro_veiculo_ja_alocado(
                dal, idmap, int(id_veiculo), id_item_excluir=id_item
            )
            if conflito is not None:
                return conflito

            conflito_mot = _erro_motorista_ja_alocado(
                dal, idmap, int(id_motorista), id_item_excluir=id_item
            )
            if conflito_mot is not None:
                return conflito_mot

            sobre = _erro_sobreposicao_motorista(
                dal,
                int(id_motorista),
                inicio_real,
                None,
                id_item_excluir=id_item,
            )
            if sobre is not None:
                return sobre

            ok = dal.update(
                """
                UPDATE tb_item_map
                SET id_linha = ?, id_veiculo = ?, id_motorista = ?,
                    hor_ini_jor = ?, hor_fim_jor = ?, chegada_ponto = ?,
                    inicio_real = COALESCE(?, inicio_real),
                    status_escala = ?
                WHERE id_item = ?
                  AND UPPER(TRIM(status_escala)) = ?
                """,
                (
                    int(id_linha),
                    int(id_veiculo),
                    int(id_motorista),
                    hor_ini,
                    hor_fim,
                    chegada,
                    inicio_real.strftime("%Y-%m-%d %H:%M:%S"),
                    STATUS_ESCALA_EM_ANDAMENTO,
                    id_item,
                    STATUS_ESCALA_EM_ANDAMENTO,
                ),
            )
            if not ok:
                conflito = _erro_veiculo_ja_alocado(
                    dal, idmap, int(id_veiculo), id_item_excluir=id_item
                )
                if conflito is not None:
                    return conflito
                conflito_mot = _erro_motorista_ja_alocado(
                    dal, idmap, int(id_motorista), id_item_excluir=id_item
                )
                if conflito_mot is not None:
                    return conflito_mot
                return MapaError("Falha ao atualizar item.", "persistencia")
    except Exception:
        return MapaError("Falha ao atualizar item.", "persistencia")

    item = _item_map_detalhe(dal, id_item)
    if item is None:
        return MapaError("Item não encontrado.", "nao_encontrado")
    return item


def _coerce_mapa_date(value: Any) -> date | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    parsed = _parse_date(value)
    if isinstance(parsed, MapaError):
        return None
    return parsed


def _parse_horario_item(
    value: Any, data_mapa: Any, campo: str
) -> datetime | None | MapaError:
    """Aceita datetime completo, HH:MM (usa data do MAPA) ou vazio → NULL."""
    if value is None:
        return None
    texto = str(value).strip()
    if not texto or texto.lower() in ("null", "none"):
        return None

    parsed = _parse_datetime_optional(texto)
    if not isinstance(parsed, MapaError):
        return parsed

    m = re.fullmatch(r"(\d{2}):(\d{2})(?::(\d{2}))?", texto)
    if m:
        base = _coerce_mapa_date(data_mapa)
        if base is None:
            return MapaError(
                f"Data do MAPA inválida para gravar {campo}.",
                "validacao",
            )
        hh, mm, ss = int(m.group(1)), int(m.group(2)), int(m.group(3) or 0)
        if hh > 23 or mm > 59 or ss > 59:
            return MapaError(f"{campo} inválido.", "validacao")
        return datetime(base.year, base.month, base.day, hh, mm, ss)

    return MapaError(f"{campo} inválido.", "validacao")


def _normalizar_horarios_item(
    payload: dict[str, Any],
    data_mapa: Any = None,
) -> tuple[datetime | None, datetime | None, datetime | None] | MapaError:
    """Converte horários do item; string vazia vira NULL (MariaDB rejeita '')."""
    hor_ini = _parse_horario_item(payload.get("hor_ini_jor"), data_mapa, "Início de jornada")
    if isinstance(hor_ini, MapaError):
        return hor_ini
    hor_fim = _parse_horario_item(payload.get("hor_fim_jor"), data_mapa, "Fim de jornada")
    if isinstance(hor_fim, MapaError):
        return hor_fim
    chegada = _parse_horario_item(payload.get("chegada_ponto"), data_mapa, "Chegada no ponto")
    if isinstance(chegada, MapaError):
        return chegada
    return hor_ini, hor_fim, chegada


def _item_map_detalhe(dal, id_item: int) -> dict[str, Any] | None:
    item_df = dal.read(
        """
        SELECT i.*,
               v.numero_frota, v.placa,
               l.codigo_linha, l.descricao AS linha,
               e.id_empresa, e.descricao AS empresa,
               mot.nome AS motorista, mot.matricula AS matricula_motorista
        FROM tb_item_map i
        INNER JOIN tb_veiculo v ON v.id_veiculo = i.id_veiculo
        INNER JOIN tb_linha l ON l.id_linha = i.id_linha
        INNER JOIN tb_empresa e ON e.id_empresa = l.id_empresa
        LEFT JOIN tb_motorista mot ON mot.id_motorista = i.id_motorista
        WHERE i.id_item = ?
        """,
        (id_item,),
    )
    if item_df.empty:
        return None
    item = item_df.iloc[0].to_dict()
    item["id_mapa_item"] = int(item["id_item"])
    st = str(item.get("status_escala") or STATUS_ESCALA_EM_ANDAMENTO).strip().upper()
    item["status_escala"] = st or STATUS_ESCALA_EM_ANDAMENTO
    item["viagens"] = []
    # TIME (hora_baixa) e timestamps do MariaDB/pandas precisam ser JSON-safe
    # (Timedelta quebra jsonify → 500 após baixa bem-sucedida).
    enriched = _enriquecer_campos_horas_item(item)
    safe = _json_safe_value(enriched)
    return safe if isinstance(safe, dict) else enriched


def excluir_item_map(dal, id_item: int) -> MapaError | None:
    dal.delete("DELETE FROM tb_viagem WHERE id_item_registro = ?", (id_item,))
    ok = dal.delete("DELETE FROM tb_item_map WHERE id_item = ?", (id_item,))
    if not ok:
        return MapaError("Item não encontrado.", "nao_encontrado")
    return None


def _normalizar_placa_hhmm(value: Any) -> str | None | MapaError:
    """Campo Placa da UI de viagem: obrigatoriamente HH:MM (5 caracteres) ou vazio."""
    if value is None:
        return None
    texto = str(value).strip()
    if not texto or texto in ("—", "-"):
        return None
    # Aceita HHMM digitado sem ':' e normaliza
    digits = "".join(ch for ch in texto if ch.isdigit())
    if len(digits) == 4 and ":" not in texto:
        texto = f"{digits[:2]}:{digits[2:]}"
    if not re.fullmatch(r"\d{2}:\d{2}", texto):
        return MapaError("Placa deve estar no formato HH:MM.", "validacao")
    hh, mm = int(texto[:2]), int(texto[3:])
    if hh > 23 or mm > 59:
        return MapaError("Placa inválida (HH:MM).", "validacao")
    return texto


def _validar_item_apto_viagem(
    dal,
    id_item: int,
    payload: dict[str, Any] | None = None,
) -> MapaError | None:
    """
    Viagem exige item existente com veículo + motorista.
    Não associa viagem só por frota/prefixo de veículo.
    """
    body = payload or {}
    # Aceita id_mapa_item / id_item no body — deve bater com a rota.
    for key in ("id_mapa_item", "id_item", "id_item_registro"):
        raw = body.get(key)
        if raw is None or str(raw).strip() == "":
            continue
        try:
            if int(raw) != int(id_item):
                return MapaError(
                    "id_mapa_item não corresponde ao item da viagem.",
                    "validacao",
                )
        except (TypeError, ValueError):
            return MapaError("id_mapa_item inválido.", "validacao")

    item = dal.read(
        """
        SELECT i.id_item, i.idmap, i.id_veiculo, i.id_motorista, i.status_escala
        FROM tb_item_map i
        WHERE i.id_item = ?
        LIMIT 1
        """,
        (int(id_item),),
    )
    if item.empty:
        return MapaError("Item não encontrado.", "nao_encontrado")

    status = str(item.iloc[0].get("status_escala") or STATUS_ESCALA_EM_ANDAMENTO)
    status = status.strip().upper() or STATUS_ESCALA_EM_ANDAMENTO
    if status == STATUS_ESCALA_ENCERRADA:
        return MapaError(
            "Esta escala recebeu baixa e não aceita novas viagens.",
            "escala_encerrada",
        )
    if status != STATUS_ESCALA_EM_ANDAMENTO:
        return MapaError(
            "Somente escalas em andamento podem registrar viagens.",
            "validacao",
        )

    idmap_raw = body.get("idmap", body.get("id_registro", body.get("id_mapa")))
    if idmap_raw is not None and str(idmap_raw).strip() != "":
        try:
            if int(idmap_raw) != int(item.iloc[0]["idmap"]):
                return MapaError(
                    "Item não pertence ao MAPA informado.",
                    "validacao",
                )
        except (TypeError, ValueError):
            return MapaError("MAPA inválido.", "validacao")

    id_veiculo = item.iloc[0]["id_veiculo"]
    id_motorista = item.iloc[0]["id_motorista"]
    if id_veiculo is None or str(id_veiculo).strip() in ("", "None", "nan"):
        return MapaError(
            "Item sem veículo vinculado. Vincule o motorista/veículo antes de registrar viagens.",
            "validacao",
        )
    try:
        if int(id_veiculo) <= 0:
            return MapaError(
                "Item sem veículo vinculado. Vincule o motorista/veículo antes de registrar viagens.",
                "validacao",
            )
    except (TypeError, ValueError):
        return MapaError(
            "Item sem veículo vinculado. Vincule o motorista/veículo antes de registrar viagens.",
            "validacao",
        )

    if id_motorista is None or str(id_motorista).strip() in ("", "None", "nan"):
        return MapaError(
            "Item sem motorista vinculado. Vincule o motorista antes de registrar viagens.",
            "validacao",
        )
    try:
        if int(id_motorista) <= 0:
            return MapaError(
                "Item sem motorista vinculado. Vincule o motorista antes de registrar viagens.",
                "validacao",
            )
    except (TypeError, ValueError):
        return MapaError(
            "Item sem motorista vinculado. Vincule o motorista antes de registrar viagens.",
            "validacao",
        )
    return None


def _horarios_viagem_do_payload(
    dal, id_item: int, payload: dict[str, Any]
) -> tuple[datetime, datetime, str | None, int, int, Any] | MapaError:
    """Resolve saída/chegada/placa(HH:MM) e quantidades — sem trocar campos."""
    apto = _validar_item_apto_viagem(dal, id_item, payload)
    if apto is not None:
        return apto

    item = dal.read(
        """
        SELECT i.id_item, m.data AS data_mapa
        FROM tb_item_map i
        INNER JOIN tb_map m ON m.id_registro = i.idmap
        WHERE i.id_item = ?
        """,
        (id_item,),
    )
    if item.empty:
        return MapaError("Item não encontrado.", "nao_encontrado")

    data_mapa = item.iloc[0]["data_mapa"]
    # Campos distintos: nao misturar placa com saida/chegada
    saida = _parse_horario_item(payload.get("horario_saida"), data_mapa, "Saída da viagem")
    if isinstance(saida, MapaError):
        return saida
    if saida is None:
        return MapaError("Saída da viagem é obrigatória.", "validacao")
    chegada = _parse_horario_item(
        payload.get("horario_chegada"), data_mapa, "Chegada da viagem"
    )
    if isinstance(chegada, MapaError):
        return chegada
    if chegada is None:
        return MapaError("Chegada da viagem é obrigatória.", "validacao")

    placa = _normalizar_placa_hhmm(payload.get("placa"))
    if isinstance(placa, MapaError):
        return placa

    qtd_pas = payload.get("qtd_passageiro", payload.get("qtd_pas_ida", 0))
    qtd_ida = qtd_pas
    qtd_volta = payload.get("qtd_pas_volta", 0)
    try:
        qtd_ida = max(0, int(qtd_ida))
        qtd_volta = max(0, int(qtd_volta))
    except (TypeError, ValueError):
        return MapaError("Quantidade de passageiros inválida.", "validacao")

    return saida, chegada, placa, qtd_ida, qtd_volta, payload.get("intervalo")


def criar_viagem(
    dal, id_item: int, payload: dict[str, Any]
) -> dict[str, Any] | MapaError:
    body = dict(payload or {})
    # Preferir body; se ausente, usar id da rota (FE envia ambos; evita 400 em clients).
    raw_mapa_item = body.get("id_mapa_item", body.get("id_item"))
    if raw_mapa_item is None or str(raw_mapa_item).strip() == "":
        raw_mapa_item = id_item
    try:
        if int(raw_mapa_item) != int(id_item):
            return MapaError(
                "id_mapa_item não corresponde ao item da viagem.",
                "validacao",
            )
    except (TypeError, ValueError):
        return MapaError("id_mapa_item inválido.", "validacao")
    body["id_mapa_item"] = int(id_item)
    body["id_item"] = int(id_item)

    horarios = _horarios_viagem_do_payload(dal, id_item, body)
    if isinstance(horarios, MapaError):
        return horarios
    saida, chegada, placa, qtd_ida, qtd_volta, intervalo = horarios

    conflito = _erro_conflito_horarios_viagem(dal, id_item, saida, chegada)
    if conflito is not None:
        return conflito

    ok = dal.create(
        """
        INSERT INTO tb_viagem (
            id_item_registro, horario_saida, horario_chegada, placa,
            intervalo, qtd_pas_ida, qtd_pas_volta
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            id_item,
            saida.strftime("%Y-%m-%d %H:%M:%S"),
            chegada.strftime("%Y-%m-%d %H:%M:%S"),
            placa,
            intervalo,
            qtd_ida,
            qtd_volta,
        ),
    )
    if not ok:
        return MapaError("Falha ao criar viagem.", "persistencia")

    row = dal.read(
        "SELECT MAX(id_viagem) AS id_viagem FROM tb_viagem WHERE id_item_registro = ?",
        (id_item,),
    )
    id_viagem = int(row.iloc[0]["id_viagem"])
    viagem_df = dal.read("SELECT * FROM tb_viagem WHERE id_viagem = ?", (id_viagem,))
    out = viagem_df.iloc[0].to_dict()
    out["id_mapa_item"] = int(id_item)
    safe = _json_safe_value(out)
    return safe if isinstance(safe, dict) else out


def atualizar_viagem(
    dal, id_viagem: int, payload: dict[str, Any]
) -> dict[str, Any] | MapaError:
    atual = dal.read(
        "SELECT id_viagem, id_item_registro FROM tb_viagem WHERE id_viagem = ?",
        (id_viagem,),
    )
    if atual.empty:
        return MapaError("Viagem não encontrada.", "nao_encontrada")

    id_item = int(atual.iloc[0]["id_item_registro"])
    horarios = _horarios_viagem_do_payload(dal, id_item, payload)
    if isinstance(horarios, MapaError):
        return horarios
    saida, chegada, placa, qtd_ida, qtd_volta, intervalo = horarios

    conflito = _erro_conflito_horarios_viagem(
        dal, id_item, saida, chegada, id_viagem_excluir=int(id_viagem)
    )
    if conflito is not None:
        return conflito

    ok = dal.update(
        """
        UPDATE tb_viagem
        SET horario_saida = ?, horario_chegada = ?, placa = ?, intervalo = ?,
            qtd_pas_ida = ?, qtd_pas_volta = ?
        WHERE id_viagem = ?
        """,
        (
            saida.strftime("%Y-%m-%d %H:%M:%S"),
            chegada.strftime("%Y-%m-%d %H:%M:%S"),
            placa,
            intervalo,
            qtd_ida,
            qtd_volta,
            id_viagem,
        ),
    )
    if not ok:
        return MapaError("Falha ao atualizar viagem.", "persistencia")

    viagem_df = dal.read("SELECT * FROM tb_viagem WHERE id_viagem = ?", (id_viagem,))
    if viagem_df.empty:
        return MapaError("Viagem não encontrada.", "nao_encontrada")
    return viagem_df.iloc[0].to_dict()


def excluir_viagem(dal, id_viagem: int) -> MapaError | None:
    ok = dal.delete("DELETE FROM tb_viagem WHERE id_viagem = ?", (id_viagem,))
    if not ok:
        return MapaError("Viagem não encontrada.", "nao_encontrada")
    return None


def listar_cadastros_mestres(dal) -> dict[str, list[dict[str, Any]]]:
    """RF-MAP-RN-004 — somente registros ativos."""
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
        "veiculos": _rows(
            dal,
            """
            SELECT id_veiculo, codigo_veiculo, numero_frota, placa, ativo, id_empresa
            FROM tb_veiculo
            WHERE ativo = 1
            ORDER BY SUBSTR(numero_frota, 2), numero_frota
            """,
        ),
        "motoristas": _rows(
            dal,
            """
            SELECT id_motorista, matricula, nome, ativo
            FROM tb_motorista
            WHERE ativo = 1
            ORDER BY matricula
            """,
        ),
    }


def _rows(dal, sql: str) -> list[dict[str, Any]]:
    df = dal.read(sql)
    if df.empty:
        return []
    records = df.to_dict(orient="records")
    # Normaliza tipos numpy/pandas para JSON (ids e flags).
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


def corrigir_escala_excepcional(
    dal,
    id_item: int,
    payload: dict[str, Any],
    executor: Any,
) -> dict[str, Any] | MapaError:
    """
    Correção excepcional (somente Admin): altera veículo/motorista após histórico.
    Exige motivo; registra before/after em tb_auditoria.
    """
    from .auditoria_service import registrar_auditoria
    from .auth_service import UsuarioAuth

    if not isinstance(executor, UsuarioAuth) or int(executor.codigo_perfil) != PERFIL_ADMIN:
        return MapaError(
            "Somente Administrador pode executar correção excepcional.",
            "perfil_negado",
        )

    motivo = str(payload.get("motivo") or "").strip()
    if not motivo:
        return MapaError("Informe o motivo da correção excepcional.", "validacao")

    atual = _item_map_detalhe(dal, int(id_item))
    if atual is None:
        return MapaError("Item não encontrado.", "nao_encontrado")

    antes = {
        "id_veiculo": atual.get("id_veiculo"),
        "numero_frota": atual.get("numero_frota"),
        "id_motorista": atual.get("id_motorista"),
        "matricula_motorista": atual.get("matricula_motorista"),
        "status_escala": atual.get("status_escala"),
    }

    id_veiculo = _resolver_id_veiculo(dal, payload) if (
        payload.get("numero_frota") or payload.get("id_veiculo")
    ) else int(atual["id_veiculo"])
    if isinstance(id_veiculo, MapaError):
        return id_veiculo

    id_motorista = _resolver_id_motorista(dal, payload) if (
        payload.get("matricula") or payload.get("id_motorista")
    ) else int(atual["id_motorista"])
    if isinstance(id_motorista, MapaError):
        return id_motorista

    ok = dal.update(
        """
        UPDATE tb_item_map
        SET id_veiculo = ?, id_motorista = ?
        WHERE id_item = ?
        """,
        (int(id_veiculo), int(id_motorista), int(id_item)),
    )
    if not ok:
        return MapaError("Falha na correção excepcional.", "persistencia")

    depois_item = _item_map_detalhe(dal, int(id_item))
    if depois_item is None:
        return MapaError("Item não encontrado após correção.", "nao_encontrado")

    registrar_auditoria(
        dal,
        entidade="escala",
        acao="corrigir",
        id_entidade=id_item,
        id_executor=executor.id_usuario,
        perfil_executor=executor.codigo_perfil,
        valores_antes=antes,
        valores_depois={
            "id_veiculo": depois_item.get("id_veiculo"),
            "numero_frota": depois_item.get("numero_frota"),
            "id_motorista": depois_item.get("id_motorista"),
            "matricula_motorista": depois_item.get("matricula_motorista"),
        },
        motivo=motivo,
    )
    return depois_item

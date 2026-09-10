"""Serviço de consulta ao cadastro corporativo de funcionários."""

from __future__ import annotations

import base64
import logging
import os
import re
import threading
from dataclasses import dataclass
from typing import Any, Protocol

logger = logging.getLogger(__name__)

MSG_MATRICULA_INVALIDA = "Matrícula deve ser numérica com no máximo 5 dígitos."
MSG_FUNCIONARIO_NAO_ENCONTRADO = (
    "Matrícula não encontrada no cadastro de funcionários."
)
MSG_ERP_INDISPONIVEL = (
    "Não foi possível consultar o cadastro corporativo no momento. Tente novamente."
)

_MATRICULA_RE = re.compile(r"^\d{1,5}$")


@dataclass(frozen=True)
class ErpError:
    mensagem: str
    codigo: str = "erp_erro"


@dataclass(frozen=True)
class ERPFuncionario:
    matricula: str
    nome: str
    foto_url: str | None
    ativo: bool
    origem: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "matricula": self.matricula,
            "nome": self.nome,
            "foto_url": self.foto_url,
            "ativo": self.ativo,
            "origem": self.origem,
        }


class ERPFuncionarioRepository(Protocol):
    origem: str

    def consultar(self, matricula: str) -> ERPFuncionario | ErpError:
        raise NotImplementedError


def normalizar_matricula(matricula: str) -> str | ErpError:
    bruto = str(matricula or "")
    normalizada = re.sub(r"\s+", "", bruto)
    if not _MATRICULA_RE.match(normalizada):
        return ErpError(MSG_MATRICULA_INVALIDA, "validacao")
    return normalizada


class MockERPFuncionarioRepository:
    """Lista fixa — SOMENTE com ERP_PROVIDER=mock (testes). Nunca usar em produção."""

    origem = "mock"

    def __init__(self, funcionarios: dict[str, Any] | None = None) -> None:
        from .erp_mock import FUNCIONARIOS_MOCK

        self._funcionarios = funcionarios or FUNCIONARIOS_MOCK

    def consultar(self, matricula: str) -> ERPFuncionario | ErpError:
        normalizada = normalizar_matricula(matricula)
        if isinstance(normalizada, ErpError):
            return normalizada

        logger.warning(
            "Consulta ERP | ERP_PROVIDER=mock | conexao_oracle=nao | "
            "tabela=lista_fixa_local | matricula=%s | aviso=nao_usar_em_producao",
            normalizada,
        )
        dado = self._funcionarios.get(normalizada)
        if dado is None and normalizada.isdigit():
            dado = self._funcionarios.get(str(int(normalizada)).zfill(5))
        if dado is None:
            logger.info(
                "Consulta ERP | ERP_PROVIDER=mock | matricula=%s | "
                "total_encontrado=0 | resultado=nao_encontrado",
                normalizada,
            )
            return ErpError(
                MSG_FUNCIONARIO_NAO_ENCONTRADO, "funcionario_nao_encontrado"
            )

        if isinstance(dado, str):
            nome = dado
            ativo = True
            foto_url = None
        else:
            nome = str(dado.get("nome") or "").strip()
            ativo = bool(dado.get("ativo", True))
            foto_url = dado.get("foto_url")

        if not nome:
            logger.info(
                "Consulta ERP | ERP_PROVIDER=mock | matricula=%s | "
                "total_encontrado=0 | resultado=nao_encontrado",
                normalizada,
            )
            return ErpError(
                MSG_FUNCIONARIO_NAO_ENCONTRADO, "funcionario_nao_encontrado"
            )

        logger.info(
            "Consulta ERP | ERP_PROVIDER=mock | matricula=%s | "
            "total_encontrado=1 | resultado=encontrado | origem=lista_fixa_local",
            normalizada,
        )
        return ERPFuncionario(
            matricula=normalizada,
            nome=nome,
            foto_url=foto_url if isinstance(foto_url, str) and foto_url else None,
            ativo=ativo,
            origem=self.origem,
        )


_SQL_FUNCIONARIO = """
        SELECT
            TO_CHAR(f.CodFunc) AS matricula,
            TRIM(f.NomeFunc) AS nome
        FROM Globus.flp_funcionarios f
        WHERE f.CodFunc = ?
        FETCH FIRST 1 ROWS ONLY
    """

_SQL_FOTO = """
        SELECT i.Imagem AS imagem
        FROM Globus.flp_funcionarios f
        INNER JOIN Globus.flp_funcionarios_imagens i
            ON i.CodIntFunc = f.CodIntFunc
        WHERE f.CodFunc = ?
        FETCH FIRST 1 ROWS ONLY
    """

_SQL_FUNCIONARIO_NAMED = """
        SELECT
            TO_CHAR(f.CodFunc) AS matricula,
            TRIM(f.NomeFunc) AS nome
        FROM Globus.flp_funcionarios f
        WHERE f.CodFunc = :matricula
        FETCH FIRST 1 ROWS ONLY
    """

_SQL_FOTO_NAMED = """
        SELECT i.Imagem AS imagem
        FROM Globus.flp_funcionarios f
        INNER JOIN Globus.flp_funcionarios_imagens i
            ON i.CodIntFunc = f.CodIntFunc
        WHERE f.CodFunc = :matricula
        FETCH FIRST 1 ROWS ONLY
    """

# Consulta RH: schema/tabela/coluna de matrícula. Sem filtro de ativo/situação —
# qualquer matrícula existente em flp_funcionarios deve ser localizável.
_ORACLE_SCHEMA = "Globus"
_ORACLE_TABELA = "flp_funcionarios"
_ORACLE_COLUNA_MATRICULA = "CodFunc"
_ORACLE_FILTRO_ATIVO = "nenhum"


def _matricula_bind(normalizada: str) -> int | str:
    """CodFunc no Globus é numérico; bind int evita mismatch com seeds/strings."""
    return int(normalizada) if normalizada.isdigit() else normalizada


def _log_consulta_oracle(
    *,
    erp_provider: str,
    conexao_aberta: bool,
    matricula: str,
    bind: Any,
    total: int,
    resultado: str,
    sql_label: str = "funcionario_por_codfunc",
) -> None:
    logger.info(
        "Consulta ERP | ERP_PROVIDER=%s | conexao_oracle=%s | "
        "schema=%s | tabela=%s | coluna_matricula=%s | filtro_ativo=%s | "
        "sql=%s | matricula=%s | bind_tipo=%s | total_encontrado=%s | resultado=%s",
        erp_provider,
        "sim" if conexao_aberta else "nao",
        _ORACLE_SCHEMA,
        f"{_ORACLE_SCHEMA}.{_ORACLE_TABELA}",
        _ORACLE_COLUNA_MATRICULA,
        _ORACLE_FILTRO_ATIVO,
        sql_label,
        matricula,
        type(bind).__name__,
        total,
        resultado,
    )


class DalERPFuncionarioRepository:
    """Consulta Oracle via DAL + erp.dat (config criptografada local)."""

    origem = "oracle"

    def __init__(self, dal: Any | None = None) -> None:
        if dal is not None:
            self._dal = dal
        else:
            from .dal_factory import get_erp_dal_instance

            self._dal = get_erp_dal_instance()

    @staticmethod
    def _col(row: Any, *names: str) -> Any:
        if row is None:
            return None
        if hasattr(row, "get"):
            for name in names:
                if name in row:
                    return row.get(name)
                upper = name.upper()
                if upper in row:
                    return row.get(upper)
                lower = name.lower()
                if lower in row:
                    return row.get(lower)
        return None

    @staticmethod
    def _blob_to_data_url(blob: Any) -> str | None:
        return OracleERPFuncionarioRepository._blob_to_data_url(blob)

    def consultar(self, matricula: str) -> ERPFuncionario | ErpError:
        normalizada = normalizar_matricula(matricula)
        if isinstance(normalizada, ErpError):
            return normalizada

        erp_provider = get_erp_provider_name()
        try:
            bind_val = _matricula_bind(normalizada)
            logger.info(
                "Consulta ERP | ERP_PROVIDER=%s | etapa=abrir_conexao | "
                "via=dal/erp.dat | matricula=%s",
                erp_provider,
                normalizada,
            )
            df = self._dal.read(_SQL_FUNCIONARIO, (bind_val,))
            total = 0 if df is None or getattr(df, "empty", True) else int(len(df))
            encontrado = total > 0
            _log_consulta_oracle(
                erp_provider=erp_provider,
                conexao_aberta=True,
                matricula=normalizada,
                bind=bind_val,
                total=total,
                resultado="encontrado" if encontrado else "nao_encontrado",
            )
            if not encontrado:
                return ErpError(
                    MSG_FUNCIONARIO_NAO_ENCONTRADO,
                    "funcionario_nao_encontrado",
                )
            row = df.iloc[0]
            nome = str(self._col(row, "nome", "NOME") or "").strip()
            if not nome:
                _log_consulta_oracle(
                    erp_provider=erp_provider,
                    conexao_aberta=True,
                    matricula=normalizada,
                    bind=bind_val,
                    total=0,
                    resultado="nao_encontrado",
                )
                return ErpError(
                    MSG_FUNCIONARIO_NAO_ENCONTRADO,
                    "funcionario_nao_encontrado",
                )
            foto_url = None
            try:
                foto_df = self._dal.read(_SQL_FOTO, (bind_val,))
                if foto_df is not None and not getattr(foto_df, "empty", True):
                    foto_url = self._blob_to_data_url(
                        self._col(foto_df.iloc[0], "imagem", "IMAGEM")
                    )
            except Exception:
                logger.warning(
                    "Foto ERP indisponível | ERP_PROVIDER=%s | matricula=%s",
                    erp_provider,
                    normalizada,
                    exc_info=True,
                )
            return ERPFuncionario(
                matricula=normalizada,
                nome=nome,
                foto_url=foto_url,
                # Sem filtro de situação no RH: registro existente = utilizável no cadastro.
                ativo=True,
                origem=self.origem,
            )
        except ErpError as exc:
            return exc
        except Exception as exc:
            logger.error(
                "Falha ao consultar cadastro corporativo | ERP_PROVIDER=%s | "
                "conexao_oracle=falha | matricula=%s | tabela=%s.%s | erro=%s",
                erp_provider,
                normalizada,
                _ORACLE_SCHEMA,
                _ORACLE_TABELA,
                type(exc).__name__,
                exc_info=True,
            )
            return ErpError(MSG_ERP_INDISPONIVEL, "erp_indisponivel")


class OracleERPFuncionarioRepository:
    origem = "oracle"
    _pool = None
    _pool_lock = threading.Lock()

    _SQL_FUNCIONARIO = _SQL_FUNCIONARIO_NAMED
    _SQL_FOTO = _SQL_FOTO_NAMED

    def __init__(self) -> None:
        self.user = (os.getenv("ERP_ORACLE_USER") or "").strip()
        self.password = os.getenv("ERP_ORACLE_PASSWORD") or ""
        self.dsn = self._build_dsn()
        self.timeout_ms = self._read_int("ERP_ORACLE_TIMEOUT_MS", 5000)
        self.pool_min = self._read_int("ERP_ORACLE_POOL_MIN", 1)
        self.pool_max = self._read_int("ERP_ORACLE_POOL_MAX", 4)
        self.pool_increment = self._read_int("ERP_ORACLE_POOL_INCREMENT", 1)

    @staticmethod
    def _read_int(env_name: str, default: int) -> int:
        raw = (os.getenv(env_name) or "").strip()
        if not raw:
            return default
        try:
            value = int(raw)
        except ValueError:
            return default
        return value if value > 0 else default

    def _build_dsn(self) -> str:
        dsn = (os.getenv("ERP_ORACLE_DSN") or "").strip()
        if dsn:
            return dsn
        host = (os.getenv("ERP_ORACLE_HOST") or "").strip()
        port = (os.getenv("ERP_ORACLE_PORT") or "1521").strip()
        service_name = (os.getenv("ERP_ORACLE_SERVICE_NAME") or "").strip()
        if not host or not service_name or not self.user or not self.password:
            raise ValueError("Oracle ERP não configurado.")
        timeout_s = max(1, self._read_int("ERP_ORACLE_TIMEOUT_MS", 5000) // 1000)
        return (
            f"{host}:{port}/{service_name}"
            f"?transport_connect_timeout={timeout_s}&expire_time=1"
        )

    def _get_pool(self):
        if self.__class__._pool is not None:
            return self.__class__._pool

        with self.__class__._pool_lock:
            if self.__class__._pool is not None:
                return self.__class__._pool
            try:
                import oracledb
            except ImportError as exc:
                raise RuntimeError("Driver Oracle não instalado.") from exc
            logger.info("Inicializando pool Oracle ERP | provider=oracle")
            self.__class__._pool = oracledb.create_pool(
                user=self.user,
                password=self.password,
                dsn=self.dsn,
                min=self.pool_min,
                max=self.pool_max,
                increment=self.pool_increment,
            )
            return self.__class__._pool

    @staticmethod
    def _blob_to_data_url(blob: Any) -> str | None:
        if blob is None:
            return None
        if isinstance(blob, (bytes, bytearray, memoryview)):
            raw = bytes(blob)
        elif hasattr(blob, "read"):
            raw = bytes(blob.read() or b"")
        else:
            return None
        if not raw:
            return None
        mime = "image/jpeg"
        if raw[:8] == b"\x89PNG\r\n\x1a\n":
            mime = "image/png"
        elif raw[:6] in (b"GIF87a", b"GIF89a"):
            mime = "image/gif"
        encoded = base64.b64encode(raw).decode("ascii")
        return f"data:{mime};base64,{encoded}"

    def consultar(self, matricula: str) -> ERPFuncionario | ErpError:
        normalizada = normalizar_matricula(matricula)
        if isinstance(normalizada, ErpError):
            return normalizada

        erp_provider = get_erp_provider_name()
        try:
            bind_val = _matricula_bind(normalizada)
            logger.info(
                "Consulta ERP | ERP_PROVIDER=%s | etapa=abrir_conexao | "
                "via=pool_oracledb | matricula=%s",
                erp_provider,
                normalizada,
            )
            pool = self._get_pool()
            with pool.acquire() as conn:
                conn.call_timeout = self.timeout_ms
                with conn.cursor() as cur:
                    cur.execute(self._SQL_FUNCIONARIO, {"matricula": bind_val})
                    row = cur.fetchone()
                    total = 0 if row is None else 1
                    _log_consulta_oracle(
                        erp_provider=erp_provider,
                        conexao_aberta=True,
                        matricula=normalizada,
                        bind=bind_val,
                        total=total,
                        resultado="encontrado" if total > 0 else "nao_encontrado",
                    )
                    if row is None:
                        return ErpError(
                            MSG_FUNCIONARIO_NAO_ENCONTRADO,
                            "funcionario_nao_encontrado",
                        )
                    nome = str(row[1] or "").strip()
                    if not nome:
                        return ErpError(
                            MSG_FUNCIONARIO_NAO_ENCONTRADO,
                            "funcionario_nao_encontrado",
                        )
                    foto_url = None
                    try:
                        cur.execute(self._SQL_FOTO, {"matricula": bind_val})
                        foto_row = cur.fetchone()
                        if foto_row is not None:
                            foto_url = self._blob_to_data_url(foto_row[0])
                    except Exception:
                        logger.warning(
                            "Foto ERP indisponível | ERP_PROVIDER=%s | matricula=%s",
                            erp_provider,
                            normalizada,
                            exc_info=True,
                        )
                    return ERPFuncionario(
                        matricula=normalizada,
                        nome=nome,
                        foto_url=foto_url,
                        ativo=True,
                        origem=self.origem,
                    )
        except ErpError as exc:
            return exc
        except Exception as exc:
            logger.error(
                "Falha ao consultar cadastro corporativo | ERP_PROVIDER=%s | "
                "conexao_oracle=falha | matricula=%s | tabela=%s.%s | erro=%s",
                erp_provider,
                normalizada,
                _ORACLE_SCHEMA,
                _ORACLE_TABELA,
                type(exc).__name__,
                exc_info=True,
            )
            return ErpError(MSG_ERP_INDISPONIVEL, "erp_indisponivel")


class ERPFuncionarioService:
    def __init__(self, repository: ERPFuncionarioRepository) -> None:
        self._repository = repository

    @property
    def provider(self) -> str:
        return self._repository.origem

    def consultar(self, matricula: str) -> dict[str, Any] | ErpError:
        resultado = self._repository.consultar(matricula)
        if isinstance(resultado, ErpError):
            return resultado
        return resultado.to_dict()

    def existe(self, matricula: str) -> bool | ErpError:
        resultado = self._repository.consultar(matricula)
        if isinstance(resultado, ErpError):
            return resultado
        return True

    def anexar_foto(self, matricula: str, destino: dict[str, Any]) -> dict[str, Any]:
        resultado = self._repository.consultar(matricula)
        if isinstance(resultado, ErpError):
            destino["foto_url"] = None
            return destino
        destino["foto_url"] = resultado.foto_url
        return destino


def _legacy_erp_enabled() -> bool:
    raw = (os.getenv("REDMAPA_ERP_ENABLED", "0") or "0").strip().lower()
    return raw in ("1", "true", "yes", "on")


def get_erp_provider_name() -> str:
    """
    Resolve o provider efetivo.
    - ERP_PROVIDER explícito tem prioridade.
    - Sem explícito: se erp.dat/env Oracle configurado → oracle.
    - Mock NUNCA é default silencioso (só com ERP_PROVIDER=mock).
    """
    explicit = (os.getenv("ERP_PROVIDER") or "").strip().lower()
    if explicit in {"oracle", "mock", "disabled"}:
        return explicit
    if _legacy_erp_enabled() or is_erp_oracle_configured():
        return "oracle" if is_erp_oracle_configured() else "disabled"
    return "disabled"


def _erp_dat_path() -> str:
    from .dal_factory import ARQUIVOS_CRIP_DIR, normalizar_config_arquivo

    cfg = normalizar_config_arquivo(os.getenv("REDMAPA_ERP_CONFIG", "erp"))
    return os.path.join(ARQUIVOS_CRIP_DIR, "arq", f"{cfg}.dat")


def is_erp_dat_configured() -> bool:
    return os.path.isfile(_erp_dat_path())


def is_erp_oracle_env_configured() -> bool:
    if (os.getenv("ERP_ORACLE_DSN") or "").strip():
        return bool(
            (os.getenv("ERP_ORACLE_USER") or "").strip()
            and (os.getenv("ERP_ORACLE_PASSWORD") or "")
        )
    return bool(
        (os.getenv("ERP_ORACLE_HOST") or "").strip()
        and (os.getenv("ERP_ORACLE_SERVICE_NAME") or "").strip()
        and (os.getenv("ERP_ORACLE_USER") or "").strip()
        and (os.getenv("ERP_ORACLE_PASSWORD") or "")
    )


def is_erp_oracle_configured() -> bool:
    return is_erp_dat_configured() or is_erp_oracle_env_configured()


def build_erp_funcionario_service() -> ERPFuncionarioService | ErpError | None:
    provider = get_erp_provider_name()
    logger.info(
        "ERP provider efetivo | ERP_PROVIDER=%s | erp.dat=%s | env_oracle=%s",
        provider,
        is_erp_dat_configured(),
        is_erp_oracle_env_configured(),
    )
    if provider == "disabled":
        return None
    if provider == "mock":
        logger.warning(
            "ERP_PROVIDER=mock ativo — lista fixa local (somente testes). "
            "Produção deve usar ERP_PROVIDER=oracle."
        )
        return ERPFuncionarioService(MockERPFuncionarioRepository())
    if provider == "oracle":
        if not is_erp_oracle_configured():
            logger.error(
                "Oracle ERP não configurado | ERP_PROVIDER=oracle | erp.dat=%s | "
                "env_dsn_ou_host=%s | path=%s",
                is_erp_dat_configured(),
                is_erp_oracle_env_configured(),
                _erp_dat_path(),
            )
            return ErpError(MSG_ERP_INDISPONIVEL, "erp_indisponivel")
        try:
            # Preferência: erp.dat — sem fallback para mock.
            if is_erp_dat_configured():
                logger.info(
                    "ERP Oracle via DAL/erp.dat | ERP_PROVIDER=oracle | path=%s | "
                    "tabela=%s.%s | coluna_matricula=%s | filtro_ativo=%s",
                    _erp_dat_path(),
                    _ORACLE_SCHEMA,
                    _ORACLE_TABELA,
                    _ORACLE_COLUNA_MATRICULA,
                    _ORACLE_FILTRO_ATIVO,
                )
                return ERPFuncionarioService(DalERPFuncionarioRepository())
            logger.info(
                "ERP Oracle via variáveis ERP_ORACLE_* | ERP_PROVIDER=oracle | "
                "tabela=%s.%s | coluna_matricula=%s | filtro_ativo=%s",
                _ORACLE_SCHEMA,
                _ORACLE_TABELA,
                _ORACLE_COLUNA_MATRICULA,
                _ORACLE_FILTRO_ATIVO,
            )
            return ERPFuncionarioService(OracleERPFuncionarioRepository())
        except Exception:
            logger.error(
                "Falha ao configurar provider Oracle ERP | ERP_PROVIDER=oracle "
                "(sem fallback mock)",
                exc_info=True,
            )
            return ErpError(MSG_ERP_INDISPONIVEL, "erp_indisponivel")
    logger.error("ERP_PROVIDER inválido | valor=%s", provider)
    return ErpError(MSG_ERP_INDISPONIVEL, "erp_indisponivel")

# ----------------------------
# Deus seja Louvado!
# ----------------------------

import os
import pandas as pd
import threading
import time
import platform
import unicodedata

from typing import Any, Dict, Optional, Sequence, Union

try:
    from CONFIGURACAO import ConfiguracaoError, clmain
except ImportError:
    from .CONFIGURACAO import ConfiguracaoError, clmain

try:
    from LOG import CLLOG
except ImportError:
    from LOG.LOG import CLLOG

# Raiz do projeto (pasta pai de DAL/), onde ficam drivers/
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# SGBD alvo: mariadb | oracle | postgresql
SGBD_PAD = "mariadb"

# Arquivo de parâmetros em arquivos_crip/arq/ (sem extensão .dat)
CONFIG_ARQ_PAD = "map_MariaDB"

_MODULO = "DAL"
_log = CLLOG()

_SGBD_ALIASES = {
    "mariadb": "mariadb",
    "mysql": "mariadb",
    "oracle": "oracle",
    "postgresql": "postgresql",
    "postgres": "postgresql",
    "postgree": "postgresql",
}


def _log_evento(descricao: str) -> None:
    _log._registrar_Evento(f"[{_MODULO}] {descricao}")


def _log_excecao(excecao: BaseException, contexto: str) -> None:
    _log._registrar_exceção(excecao, f"[{_MODULO}] {contexto}")


def _contar_parametros(values: Optional[Union[Sequence[Any], Any]]) -> int:
    if values is None:
        return 0
    if isinstance(values, (list, tuple)):
        return len(values)
    return 1


def _normalizar_nome_parametro(chave: str) -> str:
    texto = unicodedata.normalize("NFKD", str(chave))
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return texto.lower().strip().replace(" ", "_").replace("-", "_")


def _buscar_parametro(
    parametros: Dict[str, Any],
    *aliases: str,
    obrigatorio: bool = True,
    default: Any = None,
) -> Any:
    """Localiza um parâmetro no dicionário descriptografado, sem depender de ordem fixa."""
    indice = {_normalizar_nome_parametro(chave): valor for chave, valor in parametros.items()}

    for alias in aliases:
        chave_norm = _normalizar_nome_parametro(alias)
        if chave_norm in indice:
            valor = indice[chave_norm]
            if valor is not None and str(valor).strip() != "":
                return valor

    if obrigatorio:
        aliases_txt = ", ".join(aliases)
        raise ConfigurationError(
            f"Parâmetro obrigatório não encontrado no arquivo de configuração. "
            f"Aliases aceitos: {aliases_txt}"
        )

    return default


def _normalizar_sgbd(sgbd: str) -> str:
    chave = (sgbd or "").strip().lower()
    if chave not in _SGBD_ALIASES:
        suportados = ", ".join(sorted(set(_SGBD_ALIASES.values())))
        raise ConfigurationError(
            f"SGBD '{sgbd}' não suportado. Valores aceitos para SGBD_PAD: {suportados}"
        )
    return _SGBD_ALIASES[chave]


class DatabaseConnectionError(Exception):
    pass


class ConfigurationError(Exception):
    pass


class QueryCache:
    def __init__(self, ttl_seconds=300):
        self.ttl = ttl_seconds
        self._data = {}
        self._time = {}
        self._lock = threading.Lock()

    def get(self, key):
        with self._lock:
            if key in self._data:
                if time.time() - self._time[key] < self.ttl:
                    return self._data[key].copy()

                del self._data[key]
                del self._time[key]

        return None

    def set(self, key, value):
        with self._lock:
            self._data[key] = value.copy()
            self._time[key] = time.time()


class ConnectionPool:
    def __init__(self, max_connections=10):
        self.max_connections = max_connections
        self._pool = []
        self._in_use = set()
        self._lock = threading.Lock()
        self._creator = None

    def set_creator(self, creator):
        self._creator = creator

    def get_connection(self):
        with self._lock:
            for conn in self._pool:
                if conn not in self._in_use:
                    self._in_use.add(conn)
                    _log_evento(
                        f"Conexão reutilizada do pool | em_uso={len(self._in_use)} | "
                        f"total={len(self._pool)}"
                    )
                    return conn

            if len(self._pool) < self.max_connections:
                _log_evento(
                    f"Criando nova conexão no pool | total_atual={len(self._pool)} | "
                    f"maximo={self.max_connections}"
                )
                conn = self._creator()
                self._pool.append(conn)
                self._in_use.add(conn)
                return conn

            exc = DatabaseConnectionError("Pool esgotado")
            _log_excecao(
                exc,
                f"Pool de conexões esgotado | maximo={self.max_connections} | "
                f"em_uso={len(self._in_use)}",
            )
            raise exc

    def return_connection(self, conn):
        with self._lock:
            self._in_use.discard(conn)


class CircuitBreaker:
    def __init__(self, failure_threshold=5, recovery_time=30):
        self.failure_threshold = failure_threshold
        self.recovery_time = recovery_time
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"
        self._lock = threading.Lock()

    def call(self, func, *args, **kwargs):
        with self._lock:
            if self.state == "OPEN":
                if time.time() - self.last_failure_time > self.recovery_time:
                    self.state = "HALF_OPEN"
                    _log_evento(
                        f"Circuit breaker em HALF_OPEN | falhas={self.failure_count} | "
                        f"limiar={self.failure_threshold}"
                    )
                else:
                    exc = DatabaseConnectionError("Circuit breaker OPEN")
                    _log_excecao(
                        exc,
                        f"Circuit breaker aberto | falhas={self.failure_count} | "
                        f"recuperacao_em_s={self.recovery_time}",
                    )
                    raise exc

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as exc:
            self._on_failure()
            raise exc

    def _on_success(self):
        with self._lock:
            if self.state != "CLOSED":
                _log_evento(
                    f"Circuit breaker fechado após sucesso | falhas_anteriores={self.failure_count}"
                )
            self.failure_count = 0
            self.state = "CLOSED"

    def _on_failure(self):
        with self._lock:
            self.failure_count += 1
            self.last_failure_time = time.time()

            if self.failure_count >= self.failure_threshold:
                self.state = "OPEN"
                _log_evento(
                    f"Circuit breaker aberto por falhas consecutivas | "
                    f"falhas={self.failure_count} | limiar={self.failure_threshold}"
                )


class DAL:
    def __init__(
        self,
        config_arquivo: Optional[str] = None,
        pasta_conf: Optional[str] = None,
        sgbd: Optional[str] = None,
    ):
        self.config_arquivo = (config_arquivo or CONFIG_ARQ_PAD).strip()
        self.sgbd = _normalizar_sgbd(sgbd or SGBD_PAD)
        self.pasta_conf = pasta_conf

        _log_evento(
            f"Inicializando | sgbd={self.sgbd} | config_arquivo={self.config_arquivo} | "
            f"pasta_conf={self.pasta_conf or 'padrão'}"
        )

        try:
            self.config = self._carregar_configuracao()
            self.connection_string = self._montar_string_conexao()

            _log_evento(f"String de conexão montada | {self.connection_string}")

            self.cache = QueryCache()
            self.pool = ConnectionPool()
            self.pool.set_creator(self._create_connection)
            self.circuit_breaker = CircuitBreaker()

            _log_evento(f"Inicialização concluída | sgbd={self.sgbd}")
        except Exception as exc:
            _log_excecao(
                exc,
                f"Falha na inicialização | sgbd={self.sgbd} | "
                f"config_arquivo={self.config_arquivo}",
            )
            raise

    def _carregar_configuracao(self) -> Dict[str, Any]:
        try:
            leitor = clmain(self.pasta_conf)
            parametros = leitor._obter_Parametros_Configuracao(self.config_arquivo)
            _log_evento(
                f"Configuração carregada via CONFIGURACAO | arquivo={self.config_arquivo} | "
                f"total_parametros={len(parametros)}"
            )
            return parametros
        except ConfiguracaoError as exc:
            raise ConfigurationError(str(exc)) from exc

    def _montar_string_conexao(self) -> str:
        params = self.config

        if self.sgbd == "mariadb":
            host = _buscar_parametro(params, "servidor", "host", "hostname", "server", "endereco")
            port = _buscar_parametro(params, "porta", "port")
            user = _buscar_parametro(params, "usuario", "user", "username", "login")
            database = _buscar_parametro(params, "bd", "database", "db", "schema", "banco")
            return f"mariadb://{user}:***@{host}:{port}/{database}"

        if self.sgbd == "oracle":
            host = _buscar_parametro(params, "servidor", "host", "hostname", "server", "endereco")
            port = _buscar_parametro(params, "porta", "port")
            user = _buscar_parametro(params, "usuario", "user", "username", "login")
            database = _buscar_parametro(
                params,
                "bd",
                "database",
                "db",
                "service_name",
                "service name",
                "servicename",
                "sid",
                obrigatorio=False,
            )
            if database:
                return f"oracle://{user}:***@{host}:{port}/{database}"
            service = _buscar_parametro(
                params,
                "service_name",
                "service name",
                "servicename",
            )
            return f"oracle://{user}:***@{host}:{port}/?service_name={service}"

        if self.sgbd == "postgresql":
            host = _buscar_parametro(params, "servidor", "host", "hostname", "server", "endereco")
            port = _buscar_parametro(params, "porta", "port")
            user = _buscar_parametro(params, "usuario", "user", "username", "login")
            database = _buscar_parametro(params, "bd", "database", "db", "schema", "banco")
            return f"postgresql://{user}:***@{host}:{port}/{database}"

        raise ConfigurationError(f"SGBD '{self.sgbd}' não possui montagem de string de conexão.")

    def _get_oracle_client_path(self):
        if platform.system() == "Windows":
            paths = [
                os.path.join(BASE_DIR, "drivers", "oracle_win", "oracle", "instantclient_21_14"),
                os.path.join(BASE_DIR, "drivers", "oracle_win", "instantclient_21_14"),
            ]
        else:
            paths = [
                os.path.join(BASE_DIR, "drivers", "oracle_linux", "instantclient_21_1"),
            ]

        for path in paths:
            if os.path.exists(path):
                _log_evento(f"Oracle Instant Client localizado | caminho={path}")
                return path

        exc = DatabaseConnectionError(
            "Oracle Client não encontrado na pasta drivers/. "
            "Verifique drivers/oracle_win ou drivers/oracle_linux."
        )
        _log_excecao(
            exc,
            f"Oracle Instant Client não encontrado | caminhos_verificados={' | '.join(paths)}",
        )
        raise exc

    def _build_oracle_dsn(self, params: Dict[str, Any]) -> str:
        import oracledb

        host = str(_buscar_parametro(params, "servidor", "host", "hostname", "server", "endereco"))
        port = int(_buscar_parametro(params, "porta", "port"))

        database = _buscar_parametro(
            params,
            "bd",
            "database",
            "db",
            "sid",
            obrigatorio=False,
        )
        if database:
            dsn = f"{host}:{port}/{database}"
            _log_evento(f"DSN Oracle (bd/sid) montado | dsn={dsn}")
            return dsn

        service_name = _buscar_parametro(
            params,
            "service_name",
            "service name",
            "servicename",
        )
        dsn = oracledb.makedsn(host, port, service_name=str(service_name))
        _log_evento(
            f"DSN Oracle (service name) montado | host={host} | porta={port} | "
            f"service_name={service_name}"
        )
        return dsn

    def _create_connection_mariadb(self, params: Dict[str, Any]):
        import pymysql

        host = str(_buscar_parametro(params, "servidor", "host", "hostname", "server", "endereco"))
        port = int(_buscar_parametro(params, "porta", "port"))
        user = str(_buscar_parametro(params, "usuario", "user", "username", "login"))
        password = str(_buscar_parametro(params, "senha", "password", "passwd", "pwd"))
        database = str(_buscar_parametro(params, "bd", "database", "db", "schema", "banco"))

        _log_evento(f"Conectando MariaDB | host={host} | porta={port} | database={database} | user={user}")

        return pymysql.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database,
            charset="utf8mb4",
        )

    def _create_connection_oracle(self, params: Dict[str, Any]):
        import oracledb

        lib_path = self._get_oracle_client_path()

        try:
            oracledb.init_oracle_client(lib_dir=lib_path)
            oracledb.defaults.thick_mode = True
            _log_evento(f"Oracle client inicializado (thick mode) | lib_dir={lib_path}")
        except Exception as exc:
            _log_excecao(
                exc,
                f"Aviso ao inicializar Oracle client (thick mode) | lib_dir={lib_path}",
            )

        user = str(_buscar_parametro(params, "usuario", "user", "username", "login"))
        password = str(_buscar_parametro(params, "senha", "password", "passwd", "pwd"))
        dsn = self._build_oracle_dsn(params)

        _log_evento(f"Conectando Oracle | user={user} | dsn={dsn}")
        return oracledb.connect(user=user, password=password, dsn=dsn)

    def _create_connection_postgresql(self, params: Dict[str, Any]):
        host = str(_buscar_parametro(params, "servidor", "host", "hostname", "server", "endereco"))
        port = int(_buscar_parametro(params, "porta", "port"))
        user = str(_buscar_parametro(params, "usuario", "user", "username", "login"))
        password = str(_buscar_parametro(params, "senha", "password", "passwd", "pwd"))
        database = str(_buscar_parametro(params, "bd", "database", "db", "schema", "banco"))
        sslmode = _buscar_parametro(params, "sslmode", "ssl_mode", obrigatorio=False)

        _log_evento(
            f"Conectando PostgreSQL | host={host} | porta={port} | database={database} | "
            f"user={user} | sslmode={sslmode or 'padrão'}"
        )

        try:
            import psycopg2

            kwargs = {
                "host": host,
                "port": port,
                "user": user,
                "password": password,
                "dbname": database,
            }
            if sslmode:
                kwargs["sslmode"] = str(sslmode)

            return psycopg2.connect(**kwargs)
        except ImportError:
            pass

        try:
            import psycopg

            conninfo = (
                f"host={host} port={port} dbname={database} "
                f"user={user} password={password}"
            )
            if sslmode:
                conninfo += f" sslmode={sslmode}"

            return psycopg.connect(conninfo)
        except ImportError as exc:
            erro = DatabaseConnectionError(
                "Biblioteca PostgreSQL não encontrada. Instale psycopg2 ou psycopg."
            )
            _log_excecao(erro, "Driver PostgreSQL ausente (psycopg2/psycopg)")
            raise erro from exc

    def _create_connection(self):
        try:
            params = self.config

            if self.sgbd == "oracle":
                conn = self._create_connection_oracle(params)
            elif self.sgbd == "mariadb":
                conn = self._create_connection_mariadb(params)
            elif self.sgbd == "postgresql":
                conn = self._create_connection_postgresql(params)
            else:
                raise DatabaseConnectionError(f"SGBD '{self.sgbd}' não suportado")

            _log_evento(f"Conexão estabelecida com sucesso | sgbd={self.sgbd}")
            return conn
        except Exception as exc:
            _log_excecao(exc, f"Falha ao estabelecer conexão | sgbd={self.sgbd}")
            raise

    def _ajustar_sql_e_valores(
        self,
        sql: str,
        values: Optional[Union[Sequence[Any], Any]],
    ):
        if values is None:
            return sql, values

        if self.sgbd == "oracle":
            if "?" in sql:
                if isinstance(values, (list, tuple)):
                    for i in range(len(values)):
                        sql = sql.replace("?", f":{i + 1}", 1)
                else:
                    sql = sql.replace("?", ":1", 1)
                    values = [values]
            return sql, values

        if self.sgbd in ("mariadb", "postgresql") and "?" in sql:
            sql = sql.replace("?", "%s")

        return sql, values

    def execute_query(self, sql, values=None, fetch=True):
        conn = None
        cursor = None
        operacao = "SELECT" if fetch else "DML/COMMIT"
        qtd_parametros = _contar_parametros(values)

        _log_evento(
            f"Executando {operacao} | sgbd={self.sgbd} | parametros={qtd_parametros} | sql={sql}"
        )

        try:
            conn = self.circuit_breaker.call(self.pool.get_connection)
            cursor = conn.cursor()

            sql, values = self._ajustar_sql_e_valores(sql, values)

            if values is None:
                cursor.execute(sql)
            else:
                cursor.execute(sql, values)

            if fetch:
                cols = [c[0] for c in cursor.description]
                rows = cursor.fetchall()
                _log_evento(
                    f"Consulta concluída | linhas={len(rows)} | colunas={len(cols)} | "
                    f"nomes_colunas={', '.join(str(c) for c in cols)}"
                )
                return pd.DataFrame(rows, columns=cols)

            conn.commit()
            _log_evento(f"Comando executado e commit realizado | linhas_afetadas={cursor.rowcount}")
            return True

        except Exception as exc:
            _log_excecao(
                exc,
                f"Falha ao executar {operacao} | sgbd={self.sgbd} | parametros={qtd_parametros} | "
                f"sql={sql}",
            )

            if conn:
                try:
                    conn.rollback()
                    _log_evento("Rollback executado após falha na consulta")
                except Exception as rollback_exc:
                    _log_excecao(rollback_exc, "Falha ao executar rollback após erro na consulta")

            return pd.DataFrame() if fetch else False

        finally:
            if cursor:
                cursor.close()

            if conn:
                self.pool.return_connection(conn)

    def read(self, sql, values=None):
        return self.execute_query(sql, values, True)

    def create(self, sql, values=None):
        return self.execute_query(sql, values, False)

    def update(self, sql, values=None):
        return self.execute_query(sql, values, False)

    def delete(self, sql, values=None):
        return self.execute_query(sql, values, False)

    def test_connection(self):
        if self.sgbd == "oracle":
            sql = "SELECT 1 FROM DUAL"
        else:
            sql = "SELECT 1"

        _log_evento(f"Iniciando teste de conexão | sgbd={self.sgbd} | sql={sql}")
        result = self.execute_query(sql)
        sucesso = not result.empty
        _log_evento(f"Teste de conexão {'bem-sucedido' if sucesso else 'falhou'} | sgbd={self.sgbd}")
        return sucesso

    def get_sgbd(self) -> str:
        """Retorna o SGBD normalizado em uso (mariadb, oracle ou postgresql)."""
        return self.sgbd

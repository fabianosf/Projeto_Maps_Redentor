# ----------------------------
# Deus seja Louvado!
# ----------------------------
"""
Prepara ambiente PostgreSQL local (sem Docker) e aplica schema + migrations.

Uso (Windows PowerShell, na raiz do repo):
  $env:PGPASSWORD = 'sua_senha'
  .\\.venv\\Scripts\\python.exe scripts\\setup_postgresql_local.py

Variáveis (defaults alinhados ao lab local):
  PGHOST=127.0.0.1  PGPORT=5433  PGUSER=postgres  PGDATABASE=map
  REDMAPA_PG_USER / REDMAPA_PG_PASSWORD — role da aplicação (padrão = PGUSER/PGPASSWORD)
  SKIP_SEED=1 — não aplica schema_seed_lab_postgresql.sql
  SKIP_DAT=1  — não regenera map_PostGree.dat

Não apaga, recria nem trunca o banco. Idempotente.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

SCHEMA = ROOT / "database" / "schema_postgresql.sql"
SEED = ROOT / "database" / "schema_seed_lab_postgresql.sql"
MIGRATE_FILES = [
    ROOT / "database" / "schema_migrate_tb_configuracao_chave_valor_p2_postgresql.sql",
    ROOT / "database" / "schema_migrate_tb_mapa_codigo_empresa_postgresql.sql",
    ROOT / "database" / "schema_migrate_tb_map_plantao_time_postgresql.sql",
    ROOT / "database" / "schema_migrate_tb_item_map_ocupacao_completa_postgresql.sql",
    ROOT / "database" / "schema_migrate_mapa_authz_auditoria_p1_postgresql.sql",
    ROOT / "database" / "schema_migrate_frota_canonica_p1_postgresql.sql",
]


def _load_dotenv_local() -> None:
    path = ROOT / ".env.local"
    if not path.is_file():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key = key.strip()
        if key and key not in os.environ:
            os.environ[key] = val.strip().strip('"').strip("'")


def _split_statements(sql: str) -> list[str]:
    lines: list[str] = []
    for line in sql.splitlines():
        stripped = line.strip()
        if stripped.startswith("--"):
            continue
        lines.append(line)
    parts: list[str] = []
    for part in "\n".join(lines).split(";"):
        stmt = part.strip()
        if stmt and not stmt.upper().startswith("USE "):
            parts.append(stmt)
    return parts


def _is_ignorable(exc: BaseException) -> bool:
    msg = str(exc).lower()
    needles = (
        "already exists",
        "duplicate",
        "existe",
        "constraint",
    )
    # Só ignora se parecer objeto/constraint já presente — não engole erros reais.
    if "already exists" in msg:
        return True
    if "duplicate_object" in msg or "duplicateobject" in msg.replace(" ", ""):
        return True
    if "duplicate_table" in msg:
        return True
    # psycopg2: UniqueViolation on constraint name vs column — keep strict
    if "ja existe" in msg or "já existe" in msg:
        return True
    # Não usar needles genéricos sozinhos
    _ = needles
    return False


def _connect_admin():
    import psycopg2

    host = os.getenv("PGHOST", "127.0.0.1")
    port = int(os.getenv("PGPORT", "5433"))
    user = os.getenv("PGUSER", "postgres")
    password = os.getenv("PGPASSWORD", "")
    # Conecta em postgres para CREATE DATABASE
    return psycopg2.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        dbname="postgres",
    )


def _ensure_database() -> None:
    dbname = os.getenv("PGDATABASE", "map")
    app_user = os.getenv("REDMAPA_PG_USER") or os.getenv("PGUSER", "postgres")
    app_pass = os.getenv("REDMAPA_PG_PASSWORD") or os.getenv("PGPASSWORD", "")

    conn = _connect_admin()
    conn.autocommit = True
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (dbname,))
            if cur.fetchone() is None:
                cur.execute(f'CREATE DATABASE "{dbname}" ENCODING \'UTF8\' TEMPLATE template0')
                print(f"Banco criado: {dbname}")
            else:
                print(f"Banco já existe: {dbname}")

            # Role da aplicação (idempotente)
            if app_user and app_user != os.getenv("PGUSER", "postgres"):
                cur.execute("SELECT 1 FROM pg_roles WHERE rolname = %s", (app_user,))
                if cur.fetchone() is None:
                    cur.execute(
                        f"CREATE ROLE {app_user} LOGIN PASSWORD %s",
                        (app_pass,),
                    )
                    print(f"Role criada: {app_user}")
                else:
                    cur.execute(f"ALTER ROLE {app_user} PASSWORD %s", (app_pass,))
                cur.execute(f'GRANT ALL PRIVILEGES ON DATABASE "{dbname}" TO {app_user}')
    finally:
        conn.close()


def _apply_sql_file(conn, path: Path) -> None:
    sql = path.read_text(encoding="utf-8")
    statements = _split_statements(sql)
    print(f"Aplicando {path.name} ({len(statements)} statements)...")
    with conn.cursor() as cur:
        for i, stmt in enumerate(statements, 1):
            preview = " ".join(stmt.split())[:90]
            try:
                cur.execute(stmt)
                conn.commit()
                print(f"  [{i}/{len(statements)}] OK — {preview}")
            except Exception as exc:  # noqa: BLE001
                conn.rollback()
                if _is_ignorable(exc):
                    print(f"  [{i}/{len(statements)}] SKIP — {preview} ({exc})")
                    continue
                print(f"  [{i}/{len(statements)}] FALHA — {preview}", file=sys.stderr)
                raise


def _apply_via_psycopg() -> None:
    import psycopg2

    host = os.getenv("PGHOST", "127.0.0.1")
    port = int(os.getenv("PGPORT", "5433"))
    user = os.getenv("REDMAPA_PG_USER") or os.getenv("PGUSER", "postgres")
    password = os.getenv("REDMAPA_PG_PASSWORD") or os.getenv("PGPASSWORD", "")
    dbname = os.getenv("PGDATABASE", "map")

    conn = psycopg2.connect(
        host=host, port=port, user=user, password=password, dbname=dbname
    )
    try:
        _apply_sql_file(conn, SCHEMA)
        for path in MIGRATE_FILES:
            if not path.is_file():
                print(f"AVISO: migration ausente: {path}", file=sys.stderr)
                continue
            _apply_sql_file(conn, path)
        if os.getenv("SKIP_SEED", "").strip() not in ("1", "true", "yes"):
            if SEED.is_file():
                _apply_sql_file(conn, SEED)
        # Grants em schema public para role app
        with conn.cursor() as cur:
            cur.execute("GRANT ALL ON SCHEMA public TO CURRENT_USER")
            cur.execute(
                "GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO CURRENT_USER"
            )
            cur.execute(
                "GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO CURRENT_USER"
            )
        conn.commit()
    finally:
        conn.close()


def _gerar_map_postgree_dat() -> None:
    if os.getenv("SKIP_DAT", "").strip() in ("1", "true", "yes"):
        print("SKIP_DAT=1 — não regenera map_PostGree.dat")
        return

    host = os.getenv("PGHOST", "127.0.0.1")
    port = os.getenv("PGPORT", "5433")
    user = os.getenv("REDMAPA_PG_USER") or os.getenv("PGUSER", "postgres")
    password = os.getenv("REDMAPA_PG_PASSWORD") or os.getenv("PGPASSWORD", "")
    dbname = os.getenv("PGDATABASE", "map")

    if not password:
        print(
            "AVISO: PGPASSWORD vazio — map_PostGree.dat não gerado. "
            "Defina a senha e rode de novo.",
            file=sys.stderr,
        )
        return

    gac_dir = ROOT / "DAL" / "PROJ_GAC"
    if str(gac_dir) not in sys.path:
        sys.path.insert(0, str(gac_dir))
    from geradorArquivoConfiguracao import ClGAC

    gac = ClGAC(nome_arquivo="map_PostGree.dat")
    gac.definir_dados(
        {
            "sgbd": "postgresql",
            "servidor": host,
            "porta": str(port),
            "usuario": user,
            "senha": password,
            "bd": dbname,
        }
    )
    if not gac.gerarArquivoConfiguracao():
        raise SystemExit("Falha ao gerar map_PostGree.dat")
    print(f"Gerado: {gac.path_arq}/{gac.arq}")


def _smoke_dal() -> None:
    os.environ.setdefault("REDMAPA_SGBD", "postgresql")
    os.environ.setdefault("REDMAPA_CONFIG", "map_PostGree")
    from BackEnd.dal_factory import create_dal

    dal = create_dal(config_arquivo="map_PostGree", sgbd="postgresql")
    ok = dal.test_connection()
    print(f"DAL test_connection: {ok}")
    if not ok:
        raise SystemExit("Falha na conexão DAL PostgreSQL")
    df = dal.read(
        """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = 'tb_item_map'
          AND column_name IN (
            'status_escala','inicio_real','fim_real','baixa_em',
            'data_baixa','hora_baixa','duracao_trabalhada_minutos'
          )
        ORDER BY column_name
        """
    )
    cols = list(df["column_name"]) if df is not None and not df.empty else []
    print("Colunas ocupação:", ", ".join(cols) if cols else "(nenhuma)")
    required = {
        "status_escala",
        "inicio_real",
        "fim_real",
        "baixa_em",
        "duracao_trabalhada_minutos",
    }
    missing = required - set(cols)
    if missing:
        raise SystemExit(f"Colunas faltando em tb_item_map: {sorted(missing)}")


def main() -> int:
    _load_dotenv_local()
    print("=== RedMapa — setup PostgreSQL local (sem Docker) ===")
    print(
        f"Host={os.getenv('PGHOST', '127.0.0.1')} "
        f"Port={os.getenv('PGPORT', '5433')} "
        f"DB={os.getenv('PGDATABASE', 'map')}"
    )
    try:
        _ensure_database()
        _apply_via_psycopg()
        _gerar_map_postgree_dat()
        _smoke_dal()
    except Exception as exc:  # noqa: BLE001
        print(f"ERRO: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    print("OK — PostgreSQL local pronto. Use:")
    print("  REDMAPA_SGBD=postgresql REDMAPA_CONFIG=map_PostGree ERP_PROVIDER=mock")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

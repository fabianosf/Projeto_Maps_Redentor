# Banco de dados — RedMapa

O projeto mantém **MariaDB** (padrão) e **PostgreSQL** em paralelo. Os schemas MariaDB (`schema.sql`, `schema_operacional.sql`, migrações) **não** devem ser alterados para acomodar Postgres.

| SGBD | Schema de referência | Config criptografada |
|------|----------------------|----------------------|
| MariaDB | `schema.sql` + `schema_operacional.sql` (+ migrações pontuais) | `DAL/arquivos_crip/arq/map.dat` |
| PostgreSQL | `schema_postgresql.sql` (espelho atualizado) | `DAL/arquivos_crip/arq/map_PostGree.dat` |

## PostgreSQL no Linux (do zero)

### 1. Serviço e usuário

```bash
sudo pg_ctlcluster 16 main start   # ou: sudo systemctl start postgresql
# Role de app (exemplo): fabianosf com createdb + senha
```

Defina a senha **somente** em ambiente local (não versionar):

```bash
# Opção A — variável de sessão
export PGPASSWORD='sua_senha'

# Opção B — arquivo gitignored na raiz do repo
echo 'PGPASSWORD=sua_senha' > .env.local
chmod 600 .env.local
set -a && source .env.local && set +a
```

Alinhe a senha da role no cluster (via peer/socket ou como superuser):

```bash
psql -h /var/run/postgresql -d postgres -c "ALTER ROLE CURRENT_USER PASSWORD '$PGPASSWORD';"
```

### 2. Criar o banco e aplicar o schema

```bash
cd /caminho/para/Maps
createdb -h localhost -p 5432 -U fabianosf -E UTF8 --locale=pt_BR.UTF-8 map
# Se --locale falhar: createdb -h localhost -p 5432 -U fabianosf -E UTF8 -T template0 map

psql -h localhost -p 5432 -U fabianosf -d map -v ON_ERROR_STOP=1 -f database/schema_postgresql.sql
```

O arquivo `schema_postgresql.sql` já inclui autenticação (`tb_perfil` / `tb_usuario`), cadastros operacionais e as colunas finais das migrações MariaDB (`tb_chegada_saida.horario`, `tb_avaria.texto`).

Conversões aplicadas em relação ao MariaDB: `AUTO_INCREMENT`→`SERIAL`, `TINYINT(1)`→`BOOLEAN`, `DATETIME`→`TIMESTAMP`, sem `ENGINE=InnoDB`.

Diferença pragmática: `tb_configuracao.chave` é `VARCHAR(32)` no Postgres (a chave `QTD_MAX_TENTATIVAS` tem 18 caracteres; no MariaDB `VARCHAR(15)` costuma truncar em modo não-strict).

### 3. Arquivo `.dat` criptografado (PROJ_GAC)

Credenciais do banco ficam em `DAL/arquivos_crip/` (gitignored), geradas com a chave Fernet local — **nunca** hardcode de senha em arquivos versionados.

```bash
set -a && source .env.local && set +a   # garante PGPASSWORD
python3 <<'PY'
import os, sys
sys.path.insert(0, "DAL/PROJ_GAC")
from geradorArquivoConfiguracao import ClGAC

senha = os.environ.get("PGPASSWORD") or ""
if not senha:
    raise SystemExit("Defina PGPASSWORD (env ou .env.local) antes de gerar o .dat")

gac = ClGAC(nome_arquivo="map_PostGree.dat")
gac.definir_dados({
    "sgbd": "postgresql",
    "servidor": "localhost",
    "porta": "5432",
    "usuario": "fabianosf",
    "senha": senha,
    "bd": "map",
})
assert gac.gerarArquivoConfiguracao(), "Falha ao gerar map_PostGree.dat"
print("Gerado:", gac.path_arq + "/" + gac.arq)
PY
```

### 4. Subir a API com PostgreSQL

```bash
export REDMAPA_SGBD=postgresql
export REDMAPA_CONFIG=map_PostGree
# demais vars: veja BackEnd/.env.example

python -m BackEnd.app
# Health: GET http://127.0.0.1:5000/api/v1/health  → {"ok": true, ...}
```

Smoke test rápido:

```bash
REDMAPA_SGBD=postgresql REDMAPA_CONFIG=map_PostGree \
  python -c "from BackEnd.dal_factory import create_dal; print(create_dal().test_connection())"
```

## MariaDB (inalterado)

Continua o fluxo documentado em `scripts/setup_local.md`: `REDMAPA_SGBD=mariadb` (padrão) + `REDMAPA_CONFIG=map` + `map.dat`.

# RedMapa (Projeto_Maps_Redentor)

App de campo para MAPAs/plantões, escalas, viagens, ocupação, baixa e banco de horas.

- **Frontend:** React + TypeScript + Vite (`FrontEnd/`, porta `5173`)
- **Backend:** Flask (`BackEnd/`, porta `5000`)
- **Empresa (canônico):** MariaDB
- **PC local (este guia):** PostgreSQL em `127.0.0.1:5433`, **sem Docker**
- **ERP:** `ERP_PROVIDER=mock` (local) ou `oracle` (empresa). O frontend **nunca** fala com Oracle.

Timezone operacional: `America/Sao_Paulo`.

---

## Setup local com PostgreSQL (Windows)

### Pré-requisitos

- Python 3.11+
- Node.js 18+
- PostgreSQL 14+ instalado no Windows, escutando em **`127.0.0.1:5433`**
- Cliente `psql` no PATH (opcional; o script Python usa `psycopg2`)

### 1. Dependências

```powershell
cd C:\caminho\para\Maps
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt

cd FrontEnd
npm install
cd ..
```

### 2. Preparar banco + migrations + `map_PostGree.dat`

```powershell
$env:PGHOST = "127.0.0.1"
$env:PGPORT = "5433"
$env:PGUSER = "postgres"
$env:PGPASSWORD = "sua_senha_local"
$env:PGDATABASE = "map"

.\scripts\setup_postgresql_local.ps1
# ou:
.\.venv\Scripts\python.exe scripts\setup_postgresql_local.py
```

O script é **idempotente**: cria o banco `map` se faltar, aplica `database/schema_postgresql.sql` + migrations PG, seed de lab e gera `DAL/arquivos_crip/arq/map_PostGree.dat`. **Não** apaga nem trunca dados.

Migrations PostgreSQL relevantes:

- `schema_migrate_tb_item_map_ocupacao_completa_postgresql.sql` — `status_escala`, baixa, ocupação, horários reais, índices
- `schema_migrate_mapa_authz_auditoria_p1_postgresql.sql` — responsável, flags de usuário, `tb_auditoria`
- `schema_migrate_frota_canonica_p1_postgresql.sql` — frota C47/C30/D13
- `schema_migrate_tb_configuracao_chave_valor_p2_postgresql.sql` — chaves/valores longos
- (+ código MAPA / plantão TIME já existentes)

Só migrations: `python scripts/aplicar_migrate_postgresql.py` (exige `REDMAPA_SGBD=postgresql`, **sem** fallback para MariaDB).

### 3. Backend `.env`

```powershell
Copy-Item BackEnd\.env.example BackEnd\.env
```

Ajuste `BackEnd\.env`:

```env
REDMAPA_ENV=development
REDMAPA_SGBD=postgresql
REDMAPA_CONFIG=map_PostGree
ERP_PROVIDER=mock
REDMAPA_ERP_ENABLED=0
REDMAPA_HOST=127.0.0.1
REDMAPA_PORT=5000
REDMAPA_CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
FLASK_DEBUG=1
```

### 4. Subir API e frontend

```powershell
# Terminal 1 — API
.\.venv\Scripts\Activate.ps1
$env:TZ = "America/Sao_Paulo"
python -m BackEnd.app

# Terminal 2 — Vite (proxy /api → http://127.0.0.1:5000)
cd FrontEnd
npm run dev
```

Abra `http://127.0.0.1:5173`. Admin seed: matrícula **59817** / senha **123**.

### 5. Smoke

```powershell
.\.venv\Scripts\python.exe scripts\smoke_postgresql_local.py
```

---

## Troca mock ↔ Oracle (ERP)

| Ambiente | `ERP_PROVIDER` | Observação |
|----------|----------------|------------|
| PC local | `mock` | Sem Oracle; cadastro corporativo simulado |
| Empresa | `oracle` | Credenciais em `erp.dat` (nunca no frontend) |

- Funcionário encontrado: **200**
- Não encontrado: **404**
- Oracle indisponível: **503**
- Sem fallback silencioso `production` → `mock` (startup falha)

---

## MariaDB (empresa)

Continua o fluxo em `scripts/setup_local.md` e `database/README.md`:

```env
REDMAPA_SGBD=mariadb
REDMAPA_CONFIG=map
ERP_PROVIDER=oracle
```

Não misture SGBDs: `REDMAPA_SGBD` + `.dat` devem coincidir (sem fallback silencioso).

---

## Testes

```powershell
# Backend
.\.venv\Scripts\python.exe -m pytest BackEnd/tests -q

# Frontend
cd FrontEnd
npm run typecheck
npm run lint
npm run test
npm run build
```

Mais detalhes do schema: [`database/README.md`](database/README.md). Ambientes: [`docs/AMBIENTES.md`](docs/AMBIENTES.md).

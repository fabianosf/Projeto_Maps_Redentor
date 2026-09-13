## Setup local — RedMapa (Flask + React/Vite/TS)

**PostgreSQL no PC (recomendado, sem Docker):** veja [`README.md`](../README.md) e `scripts/setup_postgresql_local.ps1`.

**MariaDB (empresa / lab alternativo):** continue abaixo.

Passo a passo para subir API e frontend no Windows (PowerShell). Não cria nem altera `chave.key` / `.dat` — só indica onde ficam.

## Pré-requisitos

- Python 3.11+ (`python --version`)
- Node.js 18+ e npm (`node --version`, `npm --version`)
- MariaDB 10.6+ (ou MySQL compatível) com cliente `mysql` no PATH
- Git (opcional)

## 1. Clonar / abrir o projeto

```powershell
cd C:\Users\...\PROJ_MAP
```

## 2. Ambiente Python (venv + pip)

Na raiz do repositório:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### O que o `requirements.txt` cobre

| Pacote | Uso |
|--------|-----|
| `flask` | API (`python -m BackEnd.app`) |
| `bcrypt` | Hash/verificação de senha |
| `cryptography` | Leitura Fernet de `DAL/arquivos_crip` |
| `pandas` | Resultados SQL no DAL |
| `pymysql` | MariaDB (padrão `REDMAPA_SGBD=mariadb`) |
| `psycopg2-binary` | PostgreSQL se `REDMAPA_SGBD=postgresql` |

**Opcional (comentado no arquivo):** `oracledb` só se for usar ERP/Oracle (`ERP_PROVIDER=oracle` + `ERP_ORACLE_*`). `Pillow` só para scripts de imagem/doc.

## 3. Configuração criptografada (não versionada)

Credenciais do banco **não** vão em `.env` — ficam nos arquivos criptografados:

| Item | Caminho |
|------|---------|
| Chave Fernet | `DAL/arquivos_crip/chave/chave.key` |
| Config MariaDB (padrão) | `DAL/arquivos_crip/arq/map.dat` |
| Config ERP (legado/opcional) | `DAL/arquivos_crip/arq/erp.dat` |

Esses paths estão no `.gitignore` (`chave.key` e `*.dat`). **Não** os crie/edite por este guia se a equipe já tiver cópia local; peça os arquivos ao responsável ou use o utilitário interno da equipe (`scripts/gerar_configs_map.py` / PROJ_GAC) **fora** deste fluxo se for o caso.

O JSON interno típico de `map.dat` (após descriptografar) inclui algo como: `servidor`, `porta`, `usuario`, `senha`, `bd` (ex.: banco `map`).

## 4. Variáveis de ambiente da API

```powershell
Copy-Item BackEnd\.env.example BackEnd\.env
# Edite BackEnd\.env se precisar
```

Carregar no PowerShell da sessão atual (o Flask não lê `.env` sozinho):

```powershell
Get-Content BackEnd\.env | ForEach-Object {
  if ($_ -match '^\s*#' -or $_ -match '^\s*$') { return }
  if ($_ -match '^\s*([^=]+)=(.*)$') {
    Set-Item -Path "Env:$($matches[1].Trim())" -Value $matches[2].Trim()
  }
}
```

Variáveis (`BackEnd/app.py`):

- `REDMAPA_CONFIG` — basename em `arq/` (padrão `map`)
- `REDMAPA_SGBD` — `mariadb` \| `postgresql`
- `ERP_PROVIDER` — `mock` \| `oracle` \| `disabled`
- `REDMAPA_ERP_CONFIG` — basename do `.dat` Oracle (padrão `erp` → `erp.dat`)
- Com `ERP_PROVIDER=oracle`, preferência: `DAL/arquivos_crip/arq/erp.dat` + `chave.key`
- Alternativa sem `.dat`: `ERP_ORACLE_DSN` ou `ERP_ORACLE_HOST` / `PORT` / `SERVICE_NAME` + `USER` / `PASSWORD`
- `REDMAPA_ERP_ENABLED` — legado; mantido por compatibilidade
- `REDMAPA_COOKIE_SECURE` — `true` só com HTTPS
- `REDMAPA_HOST` / `REDMAPA_PORT` — bind (padrão `0.0.0.0:5000`)
- `FLASK_DEBUG` — `1` em desenvolvimento

## 5. Banco MariaDB

Ajuste usuário/senha do *cliente* admin conforme sua instalação. O usuário de aplicação costuma ser o definido no `map.dat` (em `schema.sql` de referência: `usumap` / banco `map`).

### 5.1 Schema fresco

Com o serviço MariaDB no ar:

```powershell
# Se FKs de tb_usuario (empresa/turno/local) falharem no schema.sql sozinho,
# rode com FOREIGN_KEY_CHECKS desligado na mesma sessão:
mysql -u root -p --init-command="SET FOREIGN_KEY_CHECKS=0;" < database\schema.sql
mysql -u root -p < database\schema_operacional.sql
mysql -u root -p < database\schema_migrate_tb_chegada_saida_horario.sql
mysql -u root -p < database\schema_migrate_tb_avaria_texto.sql
mysql -u root -p < database\schema_seed_tip_avaria.sql
mysql -u root -p < database\schema_seed_tb_indicador.sql
```

Cadastros mestres (empresas, linhas, veículos, etc.):

```powershell
mysql -u root -p < database\schema_seed.sql
```

Se `schema_seed.sql` conflitar com perfis já inseridos por `schema.sql`, use o reseed (após a API/DAL já conseguir conectar):

```powershell
python scripts\aplicar_reseed_proj_map.py
```

Admin de referência em `schema.sql`: matrícula `59492`, senha `Admin` (hash bcrypt no SQL).

### 5.2 Conferir conexão

Com venv ativo e `map.dat` + `chave.key` no lugar:

```powershell
python -c "from BackEnd.dal_factory import get_dal_instance; print('ok' if get_dal_instance().test_connection() else 'falha')"
```

## 6. Rodar a API (Flask)

Na raiz do projeto, venv ativo e env carregado:

```powershell
python -m BackEnd.app
```

Ou:

```powershell
.\scripts\dev_backend.ps1
```

Health check: [http://localhost:5000/api/v1/health](http://localhost:5000/api/v1/health) → `{"ok":true,"servico":"redmapa-api"}`.

## 7. Frontend (React + Vite + TypeScript)

```powershell
cd FrontEnd
npm install
Copy-Item .env.example .env -ErrorAction SilentlyContinue
npm run dev
```

- URL: [http://localhost:5173](http://localhost:5173)
- Em dev, o Vite faz proxy de `/api` → `http://localhost:5000` (`FrontEnd/vite.config.ts`)
- `VITE_API_URL` em `FrontEnd/.env.example` (padrão `/api/v1`); use URL absoluta só sem proxy (build/produção/celular)

### O que o `FrontEnd/package.json` cobre

- **Runtime:** React 18, React Router, Radix UI (dialog, select, tabs, etc.), Tailwind helpers (`clsx`, `cva`, `tailwind-merge`), `lucide-react`, `sonner`, `date-fns` / `react-day-picker` (disponíveis no projeto)
- **Build/dev:** Vite 5, TypeScript, `@vitejs/plugin-react`, Tailwind/PostCSS/Autoprefixer
- **Opcional:** Playwright (testes/capturas) — não é preciso para `npm run dev`

> `scripts/dev_frontend.ps1` / `setup_frontend.ps1` apontam para `C:\RedMapaDev` (cópia em disco C). Para setup local padrão use `cd FrontEnd` + `npm run dev` no próprio repositório.

## 8. Checklist rápido

1. `.venv` + `pip install -r requirements.txt`
2. `DAL/arquivos_crip/chave/chave.key` e `DAL/arquivos_crip/arq/map.dat` presentes
3. `BackEnd/.env` a partir do `.env.example` + vars no shell
4. MariaDB com `schema.sql` + `schema_operacional.sql` + migrações `horario`/`texto` + seeds
5. `python -m BackEnd.app` → health `ok`
6. `FrontEnd`: `npm install` + `npm run dev` → login na porta 5173

## Problemas comuns

| Sintoma | Causa provável |
|---------|----------------|
| Erro ao abrir `chave.key` / `.dat` | Arquivos ausentes ou chave diferente do `.dat` |
| Health `ok: false` / 503 | MariaDB parado, host/senha do `map.dat`, ou banco `map` inexistente |
| Frontend chama API e falha de rede | API fora do ar ou proxy; confirme `:5000` e `npm run dev` |
| Cadastro ERP / foto falha | Falta `oracledb` ou `ERP_ORACLE_*` (opcional; não bloqueia login local com `ERP_PROVIDER=mock`) |

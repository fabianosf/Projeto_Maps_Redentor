# ----------------------------
# Deus seja Louvado!
# ----------------------------

# Ambientes RedMapa (Fase 2)

## Visão geral

| Ambiente | SGBD | ERP | HTTPS | Dados |
|----------|------|-----|-------|-------|
| **Development (PC)** | PostgreSQL local `127.0.0.1:5433` (sem Docker) | `ERP_PROVIDER=mock` | opcional | sintéticos / seed lab |
| **Development (alt.)** | MariaDB local | `ERP_PROVIDER=mock` | opcional | sintéticos |
| **Staging / Homologação** | MariaDB isolado | mock **ou** Oracle de homolog (nunca prod) | recomendado | teste / mascarados |
| **Production** | MariaDB oficial (rede interna) | `ERP_PROVIDER=oracle` obrigatório | obrigatório | oficiais |

**Regra dura:** `REDMAPA_ENV=production` + `ERP_PROVIDER=mock` → **falha no startup**. Não há fallback silencioso de produção para mock, nem entre MariaDB ↔ PostgreSQL.

PostgreSQL é suportado para **lab local** (fluxos críticos de MAPA/escala/ocupação/baixa/banco de horas). **Canônico na empresa:** MariaDB.

---

## Variáveis por ambiente

Copie `BackEnd/.env.example` → `BackEnd/.env` (nunca versionar). Credenciais MariaDB/Oracle ficam em `DAL/arquivos_crip/` (`map.dat`, `erp.dat`, `chave.key`) no servidor — **não** no repositório.

### Development (PostgreSQL no PC — recomendado sem Docker)

```bash
REDMAPA_ENV=development
REDMAPA_SGBD=postgresql
REDMAPA_CONFIG=map_PostGree
ERP_PROVIDER=mock
REDMAPA_ERP_ENABLED=0
REDMAPA_COOKIE_SECURE=false
REDMAPA_COOKIE_SAMESITE=lax
REDMAPA_CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
FLASK_DEBUG=1
```

Preparar banco: `python scripts/setup_postgresql_local.py` (porta padrão `5433`). Ver `README.md`.

Frontend: `VITE_API_URL` omitido → proxy Vite `/api` → `http://127.0.0.1:5000`.

### Development (MariaDB)

```bash
REDMAPA_ENV=development
REDMAPA_SGBD=mariadb
REDMAPA_CONFIG=map
ERP_PROVIDER=mock
REDMAPA_COOKIE_SECURE=false
REDMAPA_COOKIE_SAMESITE=lax
REDMAPA_CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
FLASK_DEBUG=1
```

### Staging

```bash
REDMAPA_ENV=staging
REDMAPA_SGBD=mariadb
ERP_PROVIDER=oracle   # preferível; mock só com dados mascarados e aceite explícito
REDMAPA_COOKIE_SECURE=true
REDMAPA_CORS_ORIGINS=https://homolog.redmapa.exemplo
FLASK_DEBUG=0
REDMAPA_METRICS_TOKEN=<token-longo>
```

### Production

```bash
REDMAPA_ENV=production
REDMAPA_SGBD=mariadb
ERP_PROVIDER=oracle
REDMAPA_COOKIE_SECURE=true
REDMAPA_COOKIE_SAMESITE=lax   # none apenas se front e API em domínios distintos + Secure
REDMAPA_CORS_ORIGINS=https://app.redmapa.exemplo
FLASK_DEBUG=0
REDMAPA_METRICS_TOKEN=<token-longo>
```

---

## Segredos

- Nunca commit: `.env`, `*.dat`, `chave.key`, dumps com PII, `backups/`.
- CI falha se `.env` / `.dat` / `chave.key` aparecerem no índice git.
- Rotação: se qualquer segredo foi exposto, regenerar `chave.key` + recriptografar `map.dat`/`erp.dat`, trocar senhas MariaDB/Oracle e tokens de métricas **antes** de homologar.

---

## Health e métricas

- `GET /api/v1/health` — DB + ambiente + provider ERP (sem segredos).
- `GET /api/v1/metrics` — exige `X-Metrics-Token` (ou `REDMAPA_METRICS_PUBLIC=1` só em lab).
- Respostas de erro e header `X-Request-ID` carregam correlation ID.

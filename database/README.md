# Banco de dados — RedMapa

O projeto mantém **MariaDB** (padrão) e **PostgreSQL** em paralelo. Os schemas MariaDB (`schema.sql`, `schema_operacional.sql`, migrações) **não** devem ser alterados para acomodar Postgres.

| SGBD | Schema de referência | Config criptografada |
|------|----------------------|----------------------|
| MariaDB | `schema.sql` + `schema_operacional.sql` (+ migrações pontuais) | `DAL/arquivos_crip/arq/map.dat` |
| PostgreSQL | `schema_postgresql.sql` (espelho atualizado) | `DAL/arquivos_crip/arq/map_PostGree.dat` |

## PostgreSQL local (PC — sem Docker)

Porta de lab: **`127.0.0.1:5433`**. Script único (cria DB, schema, migrations, seed, `map_PostGree.dat`):

```powershell
# Windows
$env:PGHOST="127.0.0.1"; $env:PGPORT="5433"
$env:PGUSER="postgres"; $env:PGPASSWORD="sua_senha"; $env:PGDATABASE="map"
.\scripts\setup_postgresql_local.ps1
```

```bash
# Linux / macOS
export PGHOST=127.0.0.1 PGPORT=5433 PGUSER=postgres PGDATABASE=map
export PGPASSWORD='sua_senha'   # ou .env.local gitignored
python scripts/setup_postgresql_local.py
```

Migrations PG (idempotentes, sem DROP/TRUNCATE de dados):

| Arquivo | Conteúdo |
|---------|----------|
| `schema_migrate_tb_item_map_ocupacao_completa_postgresql.sql` | `status_escala`, baixa, `inicio_real`/`fim_real`, índices |
| `schema_migrate_mapa_authz_auditoria_p1_postgresql.sql` | `id_responsavel`, flags ERP, `tb_auditoria` |
| `schema_migrate_frota_canonica_p1_postgresql.sql` | frota C47/C30/D13 |
| `schema_migrate_tb_configuracao_chave_valor_p2_postgresql.sql` | `chave`/`valor` longos |
| `schema_migrate_tb_mapa_codigo_empresa_postgresql.sql` | código MAPA / seq |
| `schema_migrate_tb_map_plantao_time_postgresql.sql` | plantão TIME |

Só migrations (DAL já configurado): `python scripts/aplicar_migrate_postgresql.py`.

`schema_postgresql.sql` já espelha o estado final (ocupação, authz, auditoria, frota). Conversões vs MariaDB: `AUTO_INCREMENT`→`SERIAL`, `TINYINT(1)`→`BOOLEAN`, `DATETIME`→`TIMESTAMP`, `REGEXP`→`~`, sem `ENGINE=InnoDB` / `FROM DUAL`.

### Subir a API com PostgreSQL

```bash
export REDMAPA_SGBD=postgresql
export REDMAPA_CONFIG=map_PostGree
export ERP_PROVIDER=mock
python -m BackEnd.app
# Health: GET http://127.0.0.1:5000/api/v1/health  → {"ok": true, ...}
```

Smoke:

```bash
python scripts/smoke_postgresql_local.py
```

## MariaDB (inalterado)

Continua o fluxo documentado em `scripts/setup_local.md`: `REDMAPA_SGBD=mariadb` (padrão) + `REDMAPA_CONFIG=map` + `map.dat`.

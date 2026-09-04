# Security Audit — RedMapa BackEnd
**Data:** 2026-09-04  
**Escopo:** Auth, Users, Guia, Entrada/Saída, Mapas, Indicadores, Config  
**Critério:** correções aplicadas nesta auditoria + verificação de comportamento existente  

Legenda de criticidade: **CRÍTICA** · **ALTA** · **MÉDIA** · **BAIXA** · **OK** (conforme / sem falha)

---

## Resumo executivo

| # | Controle | Status | Criticidade |
|---|----------|--------|-------------|
| 1 | CORS explícito (sem `*`) | **Corrigido** — `flask-cors` + `REDMAPA_CORS_ORIGINS` | ALTA |
| 2 | Cookies HttpOnly / Secure / SameSite | **OK** (já existia); Secure via env | ALTA |
| 3 | Senha provisória aleatória + bcrypt | **OK** — `secrets.token_urlsafe` + `bcrypt` | CRÍTICA |
| 4 | `login_attempt_store` ativo | **OK** — bloqueio após N falhas; testes | ALTA |
| 5 | Rotas novas: validação + perfil | **OK** com nuances (ver §5) | ALTA |
| 6 | Flask-Limiter auth 10/min/IP | **Corrigido** | ALTA |
| 7 | Security headers | **Corrigido** | MÉDIA |

Login validado após as mudanças: `pytest BackEnd/tests/test_auth.py BackEnd/tests/test_security.py` (inclui `test_login_continua_funcionando`).

---

## 1. CORS

### Achado
Não havia configuração CORS no `create_app`. Em alguns ambientes o front (Vite `:5173`) depende de CORS com credentials; wildcard `*` seria inseguro com cookies.

### Correção
- Módulo `BackEnd/security.py` + `init_security(app)`
- Origens via `REDMAPA_CORS_ORIGINS` (default `http://localhost:5173,http://127.0.0.1:5173`)
- `*` é **filtrado** e nunca aplicado
- `supports_credentials=True` (necessário para `redmapa_sid`)

### Criticidade
**ALTA** (antes: ausência / risco de misconfig). Agora **mitigado**.

---

## 2. Cookies de sessão

### Achado
Já implementado em `auth_session.build_session_cookie` / `build_session_clear_cookie` e `_apply_cookie`:

| Atributo | Valor |
|----------|--------|
| HttpOnly | `True` |
| Secure | `REDMAPA_COOKIE_SECURE` ∈ {1,true,yes} |
| SameSite | `Lax` |
| Path | `/` |
| Nome | `redmapa_sid` |

### Correção
Nenhuma mudança de lógica. Testes em `test_security.py` cobrem HttpOnly/SameSite e Secure via env.

### Criticidade
**OK** / **ALTA** se Secure=false em produção HTTPS — operacional: setar `REDMAPA_COOKIE_SECURE=true`.

---

## 3. Senha provisória (create / reset)

### Achado
- `gerar_senha_provisoria()` → `secrets.token_urlsafe(12)` (`constants.py`)
- `criar_usuario` / `resetar_senha` → `hash_senha()` (bcrypt, 12 rounds)
- Texto puro só na resposta JSON uma vez (`senha_temporaria`); **não** há `SENHA_PROVISORIA = "12345"` no código

### Correção
Nenhuma. Testes: `test_users` (≠ `12345`) + `test_security` (aleatoriedade + bcrypt round-trip).

### Criticidade
**OK** (antes era CRÍTICA quando havia senha fixa — já sanado).

---

## 4. login_attempt_store

### Achado
- Contador em memória por matrícula (`login_attempt_store.py`)
- `autenticar_login`: se bloqueio ativo e falhas ≥ `QTD_MAX_TENTATIVAS` → `ativo=0` + `limite_tentativas`
- Sucesso chama `resetar_tentativas`

### Correção
Nenhuma na lógica. Cobertura: `test_auth.test_bloqueio_apos_n_tentativas` + `test_security.test_login_attempt_store_*`.

### Criticidade
**OK** / residual **MÉDIA**: store é process-local (reinicia com o worker). Aceitável para o RF atual; produção multi-worker pode exigir Redis.

---

## 5. Rotas novas — validação e perfil

| Módulo | AuthZ | Validação de entrada |
|--------|-------|----------------------|
| Guia | `@require_session` | payload (número, data BR, HH:MM, FKs) em `guia_service` |
| Entrada/Saída | `@require_session` | evento C/S, linha do usuário, carro, HH:MM |
| Mapas | `@require_mapa_access` (Admin/Despachante) | datas, FKs, `cod_map` com retry |
| Indicadores config | `@require_config_access` (Admin/Inspetor) | `id_inds` list; perfil existente |
| Indicadores `/me` | `@require_session` | só perfil da sessão (ignora query) |

### Achado / nuance
Guia e Entrada/Saída não restringem a um subconjunto de perfis além de “autenticado e ativo”. Isso alinha com telas operacionais (Admin, Despachante, Inspetor). Mapas e config de indicadores têm checagem de perfil explícita.

### Correção
Nenhuma mudança de negócio nesta auditoria (evitar alterar RN). Documentado como **aceito**.

### Criticidade
**OK** para o modelo atual. Se o produto exigir bloquear Inspetor em Guia/ES → **MÉDIA** residual (feature).

---

## 6. Flask-Limiter (auth)

### Achado
Não havia rate-limit nas rotas de autenticação (risco de brute-force além do bloqueio por matrícula).

### Correção
- `flask-limiter` em `security.limiter`
- `@limiter.limit("10 per minute")` em: `/login`, `/change-password`, `/cancel-change-password`, `/cancel-login`
- Desabilitado quando `TESTING=True` (suite pytest)

### Criticidade
**ALTA** (antes aberto). Agora **mitigado** (10 req/min/IP).

---

## 7. Security headers

### Achado
Respostas JSON sem headers defensivos.

### Correção (`after_request` em `init_security`):
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `Content-Security-Policy: default-src 'none'; frame-ancestors 'none'; base-uri 'none'`
- `Referrer-Policy: no-referrer`
- `Permissions-Policy: geolocation=(), microphone=(), camera=()`

### Criticidade
**MÉDIA** → **mitigado**. CSP é adequada para API JSON (front é origem separada).

---

## Arquivos tocados nesta auditoria

| Arquivo | Mudança |
|---------|---------|
| `BackEnd/security.py` | **Novo** — CORS, Limiter, headers |
| `BackEnd/app.py` | `init_security`; docs de env |
| `BackEnd/auth_routes.py` | `@limiter.limit("10 per minute")` |
| `BackEnd/.env.example` | `REDMAPA_CORS_ORIGINS` |
| `requirements.txt` | `flask-cors`, `flask-limiter`, pytest* |
| `BackEnd/tests/test_security.py` | **Novo** |
| `BackEnd/tests/sqlite_dal.py` | `init_security` no app de teste |

\* pytest já usado pela suíte; reafirmado no requirements.

---

## Como validar

```bash
pip install -r requirements.txt
pytest BackEnd/tests/test_auth.py BackEnd/tests/test_security.py -q
# Suite completa:
pytest --cov=BackEnd BackEnd/tests/
```

Produção (checklist):
1. `REDMAPA_COOKIE_SECURE=true` (HTTPS)
2. `REDMAPA_CORS_ORIGINS=https://seu-front`
3. `FLASK_DEBUG=0`

---

## Residual / próximos passos (não bloqueantes)

1. Rate-limit / session store em Redis se houver múltiplos workers.  
2. CSP/report-only no reverse proxy se a API e o front compartilhem domínio.  
3. Auditoria periódica de dependências (`pip-audit`).  

# ----------------------------
# Deus seja Louvado!
# ----------------------------

# Relatório Fase 2 — Qualidade, segurança, homologação e deploy

**Data:** 2026-09-12  
**Escopo:** CI/CD, ambientes, hardening, observabilidade, docs de deploy/rollback/homologação  
**Não inclui:** deploy real em produção; redesign UX amplo

---

## Entregáveis

| Item | Local |
|------|--------|
| CI GitHub Actions | `.github/workflows/ci.yml` |
| Ambientes | `docs/AMBIENTES.md` |
| Deploy + rollback | `docs/DEPLOY_E_ROLLBACK.md` |
| Checklist homologação | `docs/HOMOLOGACAO_CHECKLIST.md` |
| WSGI produção | `BackEnd/wsgi.py` + Gunicorn em `requirements.txt` |
| Observabilidade | `BackEnd/observability.py` |
| Testes Fase 2 | `BackEnd/tests/test_fase2_observability.py` |
| Auditoria anterior | `BackEnd/SECURITY_AUDIT.md` (ainda válida) |

---

## Segurança (revisão Fase 2)

| Controle | Status |
|----------|--------|
| CORS explícito (sem `*`) | OK — + headers `X-Request-ID` |
| Cookies HttpOnly / Secure / SameSite | OK — SameSite configurável; None exige Secure |
| HSTS | OK — quando `REDMAPA_COOKIE_SECURE=true` |
| Rate limit login + baixa + correção excepcional | OK |
| Sem stack trace ao cliente | OK — handler 500 genérico + `correlation_id` |
| Produção sem ERP mock | OK — `RuntimeError` no startup |
| Produção sem Flask debug / sem `app.run` | OK |
| Segredos no repositório | CI guarda `.env`/`.dat`/`chave.key` |
| Métricas | Protegidas por token |
| MariaDB/Oracle públicos | Mitigação operacional (docs) — validar no deploy |

### Rotação de segredos

Se `map.dat`, `erp.dat`, `chave.key` ou senhas vazaram em backups locais ou chats: **rotacionar antes da homologação oficial** (nova chave + recriptografia + senhas DB/ERP + `REDMAPA_METRICS_TOKEN`).

### Dependências

- Runtime: Flask, flask-cors, flask-limiter, bcrypt, cryptography, pandas, pymysql, gunicorn.
- Revisar periodicamente com `pip audit` / `npm audit` (não bloqueante nesta entrega; incluir no pipeline futuro se o time aprovar).

---

## Observabilidade

- Correlation ID: request header ou gerado; eco em `X-Request-ID` e JSON de erro.
- Logs estruturados em falhas API 5xx / client 4xx de `/api/`.
- Contadores in-memory: requests, 4xx/5xx, latência média, falhas ERP (`record_erp_failure`).
- Health enriquecido: ambiente, SGBD, provider ERP (sem credenciais).

Frontend: `ApiError.correlation_id` preservado no client; mensagens de rede/timeout/500 permanecem não técnicas.

---

## Resultados de testes (esta entrega)

| Suíte | Resultado |
|-------|-----------|
| Backend `pytest BackEnd/tests` (exceto Oracle integração) | **144 passed** |
| Frontend `tsc --noEmit` | **OK** |
| Frontend `vitest` | **60 passed** (15 files) |
| Frontend `npm run build` | **OK** |

Critérios CI: falha em migration ausente, pytest, typecheck, vitest ou build.

---

## Riscos residuais

1. **Homologação funcional ainda não executada** no staging com roteiro completo (Admin/Inspetor/Despachante).
2. **Oracle real** não validado nesta fase no ambiente de homologação — mock não substitui produção.
3. **Sessões em memória** (`session_store`) — multi-worker Gunicorn pode exigir sticky session ou store compartilhado (Redis) antes de escala horizontal.
4. **Rate limit em memória** — por processo; atrás de vários workers o limite efetivo é N×.
5. **Vitest** em alguns hosts instável com pool default — CI usa forks/`maxWorkers=2`.
6. **UX mobile-first** adiada até testes críticos verdes + aprovação (sem redesign nesta fase).
7. Credenciais locais em `backups/` (gitignored) — disciplina operacional de não copiar para remoto.

---

## Recomendação final

### **Apto para homologação**

Justificativa:

- Pré-condições P0/P1 e artefatos de segurança/CI/docs atendidos para iniciar homologação **controlada** em staging.
- Produção **ainda não** liberada: falta aceite do checklist P0/P1 em staging, validação Oracle oficial, smoke mobile 4G/5G, e decisão sobre store de sessão multi-worker.

| Destino | Veredito |
|---------|----------|
| Homologação / staging | **Apto** |
| Produção | **Não apto** até PASS completo do `docs/HOMOLOGACAO_CHECKLIST.md` + Oracle + HTTPS validado |

Próximo passo: executar o checklist de homologação, registrar evidências, e só então abrir Fase 3 (produção) ou ajustes P2 (pausas, etc.).

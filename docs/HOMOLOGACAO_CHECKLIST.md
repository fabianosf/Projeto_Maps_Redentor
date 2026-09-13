# ----------------------------
# Deus seja Louvado!
# ----------------------------

# Checklist de homologação — RedMapa (Fase 2)

**Pré-condições:** Fase 0 e P1 aprovados; CI verde; MariaDB de staging isolado; sem 404/500 em rotas críticas no smoke interno.

**Regra:** não liberar produção se qualquer cenário **P0/P1** falhar.

Registre evidências (print + `correlation_id` + data/hora) em pasta de homologação (fora do git se houver PII).

---

## Perfis

| Perfil | Foco |
|--------|------|
| Admin | Cadastro, ERP, correção excepcional, exclusão, auditoria, usuários |
| Inspetor | MAPAs do escopo (local/empresa/turno), escala, ocupação, baixa |
| Despachante | Apenas MAPAs próprios/atribuídos; bloqueios de escopo |

Motorista: **sem login** (validar mensagem/negação).

---

## Casos de aceite

### Auth / sessão
- [ ] Login OK (cookie HttpOnly; Secure em HTTPS)
- [ ] Senha incorreta / rate limit após abuso
- [ ] Logout limpa sessão
- [ ] Sessão expirada → mensagem clara (não stack)

### ERP
- [ ] Matrícula existente (Oracle ou mock mascarado) preenche cadastro
- [ ] Matrícula inexistente → 404 amigável
- [ ] ERP indisponível → 503 amigável (sem fallback mock em staging “oficial”)

### MAPA / escala / ocupação
- [ ] Criar MAPA + item (empresa, linha, frota canônica, motorista, horários)
- [ ] Frota inválida / prefixo empresa → bloqueio
- [ ] Ocupação global: veículo/motorista EM_ANDAMENTO exclusivos
- [ ] Viagens sequenciais (fim=início OK; overlap bloqueado)

### Baixa / troca / banco de horas
- [ ] Dar baixa fecha só aquela escala; item imutável
- [ ] Troca de carro = baixa A + nova escala B
- [ ] Banco de horas: minutos `[inicio_real, baixa_real)`, TZ America/Sao_Paulo, agrupamento por data do MAPA
- [ ] Turno noturno (cruzando meia-noite) coerente

### Permissões / auditoria
- [ ] Despachante não acessa MAPA alheio
- [ ] Inspetor limitado ao escopo
- [ ] Admin correção excepcional com auditoria
- [ ] Eventos de baixa/transferência na auditoria

### Rede / mobile
- [ ] Falha de rede / timeout → mensagem não técnica
- [ ] Uso em celular 4G/5G sem VPN (layout utilizável; sem travamento em Vincular Motorista / Dar Baixa)
- [ ] Sem redesign amplo nesta fase (só correções mobile-first se testes críticos verdes)

---

## Resultado da rodada

| Campo | Valor |
|-------|--------|
| Data | |
| Ambiente | staging / … |
| Build / tag | |
| Executor | |
| P0/P1 | PASS / FAIL |
| Liberar produção? | **NÃO** até PASS completo + Oracle real validado |

---

## UX/UI nesta fase

Somente após todos os testes críticos verdes: ajustes mobile-first **sem** alterar regra de negócio. Redesign amplo exige aprovação posterior (Fase 3/4).

# RedMapa — backlog visual (15 telas restantes)

Tokens e componentes base já estão em `styles/tokens.css`, Tailwind e `AppHeader` / `Button` / `EmptyState` / `Pill` / `EmpresaChip`. **Não mudar rotas nem regras de negócio** — só aparência e hierarquia.

## Auth

| Tela | O que mudar |
|------|-------------|
| **Recuperar senha** | Mesmo `AuthShell` navy + `auth-card` com filete ouro→ciano; um CTA navy; link voltar em ciano; sem Cancelar duplicado se houver. |
| **Primeiro acesso** | Idem auth; Confirmar = `variant="primary"`; outline só se for ação secundária real. |

## Mapas

| Tela | O que mudar |
|------|-------------|
| **Novo mapa** | Fundo `--surface`; header navy; Confirmar navy + Cancelar `outline`; footer com `.form-footer-sticky` (acima da tab bar); inputs `rounded-xl` / h-48. |
| **Editar mapa** | Igual novo mapa. |
| **Detalhe mapa** | Manter exclusão **aqui** + `ConfirmDialog`; empty “sem motorista” com ícone `UserPlus` + CTA “Vincular motorista”; chips de empresa via `EmpresaChip`; sem Excluir na lista. |

## Guia / Registros

| Tela | O que mudar |
|------|-------------|
| **Guia** | Surface + header navy; empty com `ClipboardList` + “Nova guia”; cards brancos; CTA único. |
| **Nova guia** | Confirmar navy / Cancelar outline; footer sticky acima da tab bar. |
| **Registros** | Hub rows com `icon-circle-navy` (como Início); sem cards cinza-azul. |
| **Chegada / Saída** | Empty próprio (`Bus`/`ArrowLeftRight`); formulário com 1 CTA primary. |
| **Banco de horas** | Surface; empty `Clock3`; pills de status com `Pill`. |
| **Indicadores** | Surface; header navy; sem hex solto nos gráficos/labels. |

## Mais / Admin

| Tela | O que mudar |
|------|-------------|
| **Mais** | Rows navy circle + título + 1 linha; logout `danger` ou outline, não segundo navy. |
| **Configuração** | Confirmar com `.form-footer-sticky` (nunca atrás da tab bar); Cancelar outline. |
| **Config. indicadores** | Idem config; lista + Salvar fixo. |
| **Cadastro de usuário** | Remover toolbar 5 botões quadrados; lista pesquisável + formulário; **Salvar** fixo; **Deletar/Reset** no menu `⋯`; empty `Users`. |

## Checklist transversal

1. Trocar `SCREEN_BG` legado / `AUTH_BG` claro → `SCREEN_BG` / `AUTH_BG` dos tokens novos (já apontam surface/navy).
2. Substituir `bg-slate-*` / hex inline por `bg-surface`, `text-text`, `text-text-muted`, `brand-*`.
3. `EmptyState`: sempre passar `icon` contextual.
4. Um CTA primary por tela; secundário = `outline`.
5. Header sempre `bg-brand-navy` (`AppHeader` / `OpsPageHeader`).
6. Contraste AA, foco `ring-brand-cyan` / `ring-ring`, alvos ≥44px.

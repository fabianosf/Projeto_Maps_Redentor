// ----------------------------
// Deus seja Louvado!
// ----------------------------

/**
 * Design System RedMapa — App de Campo Robusto (JS).
 * Hex só aqui e em styles/tokens.css — componentes usam classes / CSS vars.
 */

export const BRAND = {
  navy: '#003B6F',
  navyDeep: '#002A50',
  cta: '#006CC4',
  ctaDeep: '#0057A0',
  cyan: '#006CC4',
  gold: '#B45309',
  barra: '#C2410C',
  futuro: '#1D4ED8',
} as const;

export const SURFACE = '#EEF2F6';
export const SURFACE_CARD = '#FFFFFF';
export const TEXT = '#102A43';
export const TEXT_MUTED = '#486581';
export const BORDER = '#C9D5E1';
export const DANGER = '#B91C1C';
export const OK = '#15803D';
export const WARNING = '#B45309';

/** Fundo operacional da app (= --surface). */
export const SCREEN_BG = SURFACE;
export const SCREEN_BG_OPS = SURFACE;
/** Auth: navy institucional. */
export const AUTH_BG = BRAND.navy;
export const SCREEN_BG_ALT = SURFACE;
export const SURFACE_WHITE = SURFACE_CARD;
export const TABLE_HEAD_BG = '#DCE4EE';
export const TABLE_ZEBRA_BG = '#EEF2F6';

export const palette = {
  primary: BRAND.navy,
  primaryForeground: '#FFFFFF',
  cta: BRAND.cta,
  background: SURFACE,
  foreground: TEXT,
  muted: TEXT_MUTED,
  border: BORDER,
  success: OK,
  warning: WARNING,
  danger: DANGER,
  info: BRAND.cta,
} as const;

export const space = {
  0: 0,
  1: 8,
  2: 16,
  3: 24,
  4: 32,
  5: 40,
  6: 48,
  8: 64,
} as const;

export const radius = {
  sm: 8,
  md: 12,
  lg: 12,
  xl: 12,
  full: 9999,
} as const;

export const touch = {
  min: 48,
  input: 48,
  cta: 48,
} as const;

export const ui = {
  screen: 'bg-surface text-text',
  screenOps: 'bg-surface text-text',
  page: 'page flex min-h-dvh flex-col bg-surface text-text',
  pageOps: 'page flex min-h-dvh flex-col bg-surface text-text',
  pageBody: 'page-body',
  surface:
    'rounded-xl border border-border bg-surface-card text-text shadow-card',
  authCard: 'auth-card p-6',
  section:
    'flex flex-col gap-3 rounded-xl border border-border bg-surface-card p-4 shadow-card',
  sectionTitle: 'text-[13px] font-bold uppercase tracking-wide text-brand-navy',
  helper: 'text-[14px] leading-snug text-text-muted',
  fieldError: 'text-[14px] font-medium text-danger',
  tableHead: 'bg-table-head text-text',
  tableZebra: 'even:bg-table-zebra odd:bg-surface-card',
} as const;

/** Tom de marca por empresa (chip/ponto). */
export type EmpresaBrand = 'redentor' | 'barra' | 'futuro' | 'default';

export function empresaBrand(nome?: string | null): EmpresaBrand {
  const n = String(nome ?? '')
    .trim()
    .toLowerCase();
  if (n.includes('barra')) return 'barra';
  if (n.includes('futuro')) return 'futuro';
  if (n.includes('reden') || n.includes('redmapa') || n === 'red') {
    return 'redentor';
  }
  return 'default';
}

export const empresaBrandDotClass: Record<EmpresaBrand, string> = {
  redentor: 'bg-brand-cta',
  barra: 'bg-brand-barra',
  futuro: 'bg-brand-futuro',
  default: 'bg-brand-navy',
};

/** Status operacionais padronizados (sempre com texto). */
export const STATUS_LABELS = {
  EM_ANDAMENTO: 'EM ANDAMENTO',
  ENCERRADA: 'ENCERRADA',
  RASCUNHO: 'RASCUNHO',
  CANCELADA: 'CANCELADA',
  DISPONIVEL: 'DISPONÍVEL',
  OCUPADO: 'OCUPADO',
  ATENCAO: 'ATENÇÃO',
  CONFLITO: 'CONFLITO',
  PENDENTE: 'PENDENTE',
} as const;

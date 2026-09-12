// ----------------------------
// Deus seja Louvado!
// ----------------------------

/**
 * Design System RedMapa — tokens canônicos (JS).
 * Hex só aqui e em styles/tokens.css — componentes usam classes / CSS vars.
 */

export const BRAND = {
  navy: '#0B2A4A',
  navyDeep: '#071C33',
  cyan: '#00A8E0',
  gold: '#C9A227',
  barra: '#E87722',
  futuro: '#2E6BFF',
} as const;

export const SURFACE = '#F4F7FB';
export const SURFACE_CARD = '#FFFFFF';
export const TEXT = '#122033';
export const TEXT_MUTED = '#5B6B7C';
export const DANGER = '#C63A3A';
export const OK = '#1F9D5A';

/** Fundo operacional da app (= --surface). */
export const SCREEN_BG = SURFACE;
export const SCREEN_BG_OPS = SURFACE;
/** Auth: navy institucional. */
export const AUTH_BG = BRAND.navy;
export const SCREEN_BG_ALT = SURFACE;
export const SURFACE_WHITE = SURFACE_CARD;
export const TABLE_HEAD_BG = '#DCE4EE';
export const TABLE_ZEBRA_BG = '#EEF2F7';

export const palette = {
  primary: BRAND.navy,
  primaryForeground: '#FFFFFF',
  background: SURFACE,
  foreground: TEXT,
  muted: TEXT_MUTED,
  border: '#D0DAE4',
  success: OK,
  warning: BRAND.gold,
  danger: DANGER,
  info: BRAND.cyan,
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
  lg: 16,
  xl: 20,
  full: 9999,
} as const;

export const touch = {
  min: 44,
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
    'rounded-xl border border-border/60 bg-surface-card text-text shadow-card',
  authCard: 'auth-card p-6',
  section:
    'flex flex-col gap-3 rounded-xl border border-border/60 bg-surface-card p-4 shadow-sm',
  sectionTitle: 'text-[13px] font-bold uppercase tracking-wide text-brand-navy',
  helper: 'text-[13px] leading-snug text-text-muted',
  fieldError: 'text-[13px] font-medium text-danger',
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
  redentor: 'bg-brand-cyan',
  barra: 'bg-brand-barra',
  futuro: 'bg-brand-futuro',
  default: 'bg-brand-navy',
};

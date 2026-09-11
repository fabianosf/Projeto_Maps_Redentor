// ----------------------------
// Deus seja Louvado!
// ----------------------------

/**
 * Design System RedMapa — tokens canônicos.
 * Espaçamento em múltiplos de 8 px. Não altera contratos de API.
 */

export const SCREEN_BG = '#B9C8D4';
export const SCREEN_BG_OPS = SCREEN_BG;
export const AUTH_BG = '#EEF3F8';
export const SCREEN_BG_ALT = '#E4ECF5';
export const SURFACE_WHITE = '#FFFFFF';
export const TABLE_HEAD_BG = '#A8B9C9';
export const TABLE_ZEBRA_BG = '#E8EEF4';

/** Paleta institucional e semântica. */
export const palette = {
  primary: '#004587',
  primaryForeground: '#FFFFFF',
  background: '#F7FAFC',
  foreground: '#1A2332',
  muted: '#5B6B7C',
  border: '#D0DAE4',
  success: '#1F7A4D',
  warning: '#B86E00',
  danger: '#B42318',
  info: '#0B6BCB',
} as const;

/** Escala 8 px. */
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

/** Classes Tailwind semânticas (preferir em vez de hex inline). */
export const ui = {
  screen: 'bg-background text-foreground',
  screenOps: 'bg-screen text-foreground',
  page: 'page flex min-h-dvh flex-col bg-background text-foreground',
  pageOps: 'page flex min-h-dvh flex-col bg-screen text-foreground',
  pageBody: 'page-body',
  surface:
    'rounded-2xl border border-border/70 bg-card text-card-foreground shadow-card',
  authCard:
    'rounded-2xl border border-border/60 bg-card p-6 shadow-card text-card-foreground',
  section: 'flex flex-col gap-3 rounded-2xl border border-border/70 bg-card p-4 shadow-sm',
  sectionTitle: 'text-[13px] font-bold uppercase tracking-wide text-primary',
  helper: 'text-[13px] leading-snug text-muted-foreground',
  fieldError: 'text-[13px] font-medium text-destructive',
  tableHead: 'bg-table-head text-foreground',
  tableZebra: 'even:bg-table-zebra odd:bg-card',
} as const;

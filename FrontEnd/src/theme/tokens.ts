// ----------------------------
// Deus seja Louvado!
// ----------------------------

/** Tokens visuais RedMapa — interface corporativa (não alterar contratos de API). */

export const SCREEN_BG = '#B9C8D4';
export const SCREEN_BG_ALT = '#B0C4DE';

export const TABLE_HEAD_BG = '#A8B9C9';
export const TABLE_ZEBRA_BG = '#E8EEF4';
export const SURFACE_WHITE = '#FFFFFF';

/** Classes Tailwind semânticas (preferir em vez de hex inline). */
export const ui = {
  screen: 'bg-screen text-foreground',
  page: 'page flex min-h-dvh flex-col bg-screen text-foreground',
  pageBody: 'page-body bg-screen',
  surface:
    'rounded-xl border border-border/80 bg-card text-card-foreground shadow-sm',
  tableHead: 'bg-table-head text-foreground',
  tableZebra: 'even:bg-table-zebra odd:bg-card',
  filterBar: 'flex flex-col gap-3 sm:flex-row sm:flex-wrap sm:items-end',
  section: 'flex flex-col gap-3 rounded-xl border border-border/70 bg-card/80 p-4',
  sectionTitle: 'text-[13px] font-bold uppercase tracking-wide text-primary',
} as const;

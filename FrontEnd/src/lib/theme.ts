/**
 * Design System RedMapa — App de Campo Robusto.
 * Espelhados em styles/tokens.css e theme/tokens.ts.
 */
import {
  BRAND,
  SURFACE,
  TEXT,
  TEXT_MUTED,
  DANGER,
  OK,
  WARNING,
  BORDER,
} from '@/theme/tokens';

export const theme = {
  colors: {
    background: SURFACE,
    foreground: TEXT,
    primary: BRAND.navy,
    primaryForeground: '#FFFFFF',
    cta: BRAND.cta,
    secondary: '#E4EBF2',
    muted: '#EEF2F6',
    mutedForeground: TEXT_MUTED,
    border: BORDER,
    destructive: DANGER,
    success: OK,
    warning: WARNING,
    info: BRAND.cta,
    zebra: '#F5F7FA',
    brand: BRAND,
  },
  fontFamily: 'Calibri, "Segoe UI", system-ui, -apple-system, sans-serif',
  radius: {
    sm: 8,
    md: 12,
    lg: 12,
    button: 12,
    input: 12,
    modal: 12,
    card: 12,
  },
  space: {
    xs: 8,
    sm: 16,
    md: 24,
    lg: 32,
    xl: 40,
  },
  layout: {
    maxWidth: 720,
    touchMin: 48,
    inputHeight: 48,
    toolbarButtonHeight: 78,
  },
} as const;

export type Theme = typeof theme;

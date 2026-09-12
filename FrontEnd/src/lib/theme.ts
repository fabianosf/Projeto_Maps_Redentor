/**
 * Design System RedMapa — tokens canônicos (JS).
 * Espelhados em styles/tokens.css e theme/tokens.ts.
 */
import { BRAND, SURFACE, TEXT, TEXT_MUTED, DANGER, OK } from '@/theme/tokens';

export const theme = {
  colors: {
    background: SURFACE,
    foreground: TEXT,
    primary: BRAND.navy,
    primaryForeground: '#FFFFFF',
    secondary: '#E8EEF5',
    muted: '#F1F5F9',
    mutedForeground: TEXT_MUTED,
    border: '#D0DAE4',
    destructive: DANGER,
    success: OK,
    warning: BRAND.gold,
    info: BRAND.cyan,
    zebra: '#F5F7FA',
    brand: BRAND,
  },
  fontFamily: 'Calibri, "Segoe UI", system-ui, -apple-system, sans-serif',
  radius: {
    sm: 8,
    md: 12,
    lg: 16,
    button: 16,
    input: 16,
    modal: 20,
    card: 20,
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
    touchMin: 44,
    inputHeight: 48,
    toolbarButtonHeight: 78,
  },
} as const;

export type Theme = typeof theme;

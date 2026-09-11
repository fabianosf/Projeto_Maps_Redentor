/**
 * Design System RedMapa — tokens canônicos (JS).
 * Espelhados em styles/globals.css e theme/tokens.ts.
 */
export const theme = {
  colors: {
    background: '#F7FAFC',
    foreground: '#1A2332',
    primary: '#004587',
    primaryForeground: '#FFFFFF',
    secondary: '#E8EEF5',
    muted: '#F1F5F9',
    mutedForeground: '#5B6B7C',
    border: '#D0DAE4',
    destructive: '#B42318',
    success: '#1F7A4D',
    warning: '#B86E00',
    info: '#0B6BCB',
    zebra: '#F5F7FA',
  },
  fontFamily: 'Calibri, "Segoe UI", system-ui, -apple-system, sans-serif',
  radius: {
    sm: 8,
    md: 12,
    lg: 16,
    button: 12,
    input: 12,
    modal: 16,
    card: 16,
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

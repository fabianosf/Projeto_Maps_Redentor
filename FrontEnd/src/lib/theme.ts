/**
 * Design System RedMapa — tokens canônicos.
 * CSS variables espelhadas em styles/globals.css (shadcn).
 */
export const theme = {
  colors: {
    background: '#FFFFFF',
    foreground: '#1A1F2B',
    primary: '#004587',
    primaryForeground: '#FFFFFF',
    secondary: '#F2F5F8',
    muted: '#F4F6F8',
    mutedForeground: '#5C6675',
    border: '#CED4DC',
    destructive: '#B00020',
    zebra: '#F5F7FA',
  },
  fontFamily: 'Calibri, system-ui, -apple-system, sans-serif',
  radius: {
    button: 8,
    input: 8,
    modal: 12,
    toolbar: 12,
  },
  space: {
    xs: 8,
    sm: 12,
    md: 16,
    lg: 24,
    xl: 32,
  },
  layout: {
    maxWidth: 720,
    touchMin: 44,
    inputHeight: 48,
    toolbarButtonHeight: 78,
  },
} as const;

export type Theme = typeof theme;

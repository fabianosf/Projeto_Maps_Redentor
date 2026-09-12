import type { Config } from 'tailwindcss';
import animate from 'tailwindcss-animate';

/** rgb(var(--x-rgb) / <alpha-value>) — opacidade Tailwind estável. */
const rgb = (name: string) => `rgb(var(--${name}-rgb) / <alpha-value>)`;

const config: Config = {
  darkMode: ['class'],
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        border: 'hsl(var(--border) / <alpha-value>)',
        input: 'hsl(var(--input) / <alpha-value>)',
        ring: 'hsl(var(--ring) / <alpha-value>)',
        background: 'hsl(var(--background) / <alpha-value>)',
        foreground: 'hsl(var(--foreground) / <alpha-value>)',
        surface: {
          DEFAULT: rgb('surface'),
          card: rgb('surface-card'),
        },
        text: {
          DEFAULT: rgb('text'),
          muted: rgb('text-muted'),
        },
        brand: {
          navy: rgb('brand-navy'),
          'navy-deep': rgb('brand-navy-deep'),
          cyan: rgb('brand-cyan'),
          gold: rgb('brand-gold'),
          barra: rgb('brand-barra'),
          futuro: rgb('brand-futuro'),
        },
        danger: rgb('danger'),
        ok: rgb('ok'),
        screen: {
          DEFAULT: 'hsl(var(--screen) / <alpha-value>)',
          foreground: 'hsl(var(--screen-foreground) / <alpha-value>)',
        },
        primary: {
          DEFAULT: 'hsl(var(--primary) / <alpha-value>)',
          foreground: 'hsl(var(--primary-foreground) / <alpha-value>)',
        },
        secondary: {
          DEFAULT: 'hsl(var(--secondary) / <alpha-value>)',
          foreground: 'hsl(var(--secondary-foreground) / <alpha-value>)',
        },
        destructive: {
          DEFAULT: 'hsl(var(--destructive) / <alpha-value>)',
          foreground: 'hsl(var(--destructive-foreground) / <alpha-value>)',
        },
        success: {
          DEFAULT: 'hsl(var(--success) / <alpha-value>)',
          foreground: 'hsl(var(--success-foreground) / <alpha-value>)',
        },
        warning: {
          DEFAULT: 'hsl(var(--warning) / <alpha-value>)',
          foreground: 'hsl(var(--warning-foreground) / <alpha-value>)',
        },
        info: {
          DEFAULT: 'hsl(var(--info) / <alpha-value>)',
          foreground: 'hsl(var(--info-foreground) / <alpha-value>)',
        },
        muted: {
          DEFAULT: 'hsl(var(--muted) / <alpha-value>)',
          foreground: 'hsl(var(--muted-foreground) / <alpha-value>)',
        },
        accent: {
          DEFAULT: 'hsl(var(--accent) / <alpha-value>)',
          foreground: 'hsl(var(--accent-foreground) / <alpha-value>)',
        },
        card: {
          DEFAULT: 'hsl(var(--card) / <alpha-value>)',
          foreground: 'hsl(var(--card-foreground) / <alpha-value>)',
        },
        'table-head': 'hsl(var(--table-head) / <alpha-value>)',
        'table-zebra': 'hsl(var(--table-zebra) / <alpha-value>)',
      },
      boxShadow: {
        card: 'var(--shadow-card)',
      },
      borderRadius: {
        lg: 'var(--radius)',
        md: 'calc(var(--radius) - 2px)',
        sm: 'calc(var(--radius) - 4px)',
        xl: 'var(--radius-lg)',
      },
      fontFamily: {
        sans: ['Calibri', 'Segoe UI', 'system-ui', '-apple-system', 'sans-serif'],
      },
      fontSize: {
        'page-title': ['17px', { lineHeight: '1.25', fontWeight: '700' }],
        section: ['13px', { lineHeight: '1.3', fontWeight: '700' }],
      },
      maxWidth: {
        phone: '720px',
        content: '640px',
      },
      minHeight: {
        touch: 'var(--touch-min)',
        btn: 'var(--btn-height)',
      },
      height: {
        btn: 'var(--btn-height)',
      },
      spacing: {
        section: '1.25rem',
      },
    },
  },
  plugins: [animate],
};

export default config;

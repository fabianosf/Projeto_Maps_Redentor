import type { ReactNode } from 'react';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '@/lib/utils';
import {
  empresaBrand,
  empresaBrandDotClass,
  type EmpresaBrand,
} from '@/theme/tokens';

const pillVariants = cva(
  'inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-semibold tracking-wide',
  {
    variants: {
      tone: {
        neutral: 'border-border bg-muted text-text',
        ok: 'border-ok/30 bg-ok/10 text-ok',
        info: 'border-brand-cyan/30 bg-brand-cyan/10 text-brand-navy',
        danger: 'border-danger/30 bg-danger/10 text-danger',
        gold: 'border-brand-gold/40 bg-brand-gold/10 text-text',
        navy: 'border-brand-navy/20 bg-brand-navy/5 text-brand-navy',
      },
    },
    defaultVariants: {
      tone: 'neutral',
    },
  },
);

type PillProps = {
  label: string;
  className?: string;
  icon?: ReactNode;
} & VariantProps<typeof pillVariants>;

/** Pill / status compacto. */
export function Pill({ label, tone, icon, className }: PillProps) {
  return (
    <span className={cn(pillVariants({ tone }), className)} role="status">
      {icon}
      <span>{label}</span>
    </span>
  );
}

type EmpresaChipProps = {
  empresa?: string | null;
  className?: string;
  brand?: EmpresaBrand;
};

/**
 * Chip da empresa: ponto na cor da marca + nome.
 * Header permanece navy; só o ponto muda (Redentor ciano, Barra laranja, Futuro azul).
 */
export function EmpresaChip({ empresa, brand, className }: EmpresaChipProps) {
  const tone = brand ?? empresaBrand(empresa);
  const nome = String(empresa ?? '').trim() || '—';
  return (
    <span
      className={cn(
        'inline-flex max-w-full items-center gap-1.5 rounded-full border border-border/70 bg-surface px-2 py-0.5 text-xs font-semibold text-text',
        className,
      )}
    >
      <span
        className={cn('h-2 w-2 shrink-0 rounded-full', empresaBrandDotClass[tone])}
        aria-hidden
      />
      <span className="truncate">{nome}</span>
    </span>
  );
}

export { pillVariants };

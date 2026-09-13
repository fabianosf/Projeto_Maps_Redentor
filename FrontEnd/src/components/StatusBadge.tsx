import type { ReactNode } from 'react';
import { cva, type VariantProps } from 'class-variance-authority';
import {
  AlertCircle,
  CheckCircle2,
  CircleDashed,
  Clock3,
  PauseCircle,
  XCircle,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { STATUS_LABELS } from '@/theme/tokens';

const statusBadgeVariants = cva(
  'inline-flex max-w-full items-center gap-1.5 rounded-xl border px-2.5 py-1.5 text-xs font-bold uppercase tracking-wide',
  {
    variants: {
      tone: {
        neutral: 'border-field bg-surface text-text',
        info: 'border-brand-cta/40 bg-brand-cta/10 text-brand-navy',
        success: 'border-ok/40 bg-ok/10 text-ok',
        warning: 'border-warn/40 bg-warn/10 text-warn',
        danger: 'border-danger/40 bg-danger/10 text-danger',
        primary: 'border-brand-navy/30 bg-brand-navy/10 text-brand-navy',
      },
    },
    defaultVariants: {
      tone: 'neutral',
    },
  },
);

const ICONS = {
  ok: CheckCircle2,
  erro: XCircle,
  alerta: AlertCircle,
  pendente: CircleDashed,
  pausa: PauseCircle,
  tempo: Clock3,
} as const;

/** Mapeia status operacional → rótulo + tom + ícone. */
export function resolveStatusPresentation(raw?: string | null): {
  label: string;
  tone: NonNullable<VariantProps<typeof statusBadgeVariants>['tone']>;
  icon: keyof typeof ICONS;
} {
  const key = String(raw ?? '')
    .trim()
    .toUpperCase()
    .replace(/\s+/g, '_');

  if (
    key.includes('ANDAMENTO') ||
    key === 'EM_ANDAMENTO' ||
    key === 'ABERTA' ||
    key === 'ATIVA'
  ) {
    return { label: STATUS_LABELS.EM_ANDAMENTO, tone: 'info', icon: 'tempo' };
  }
  if (key.includes('ENCERR') || key === 'FECHADA' || key === 'CONCLUID') {
    return { label: STATUS_LABELS.ENCERRADA, tone: 'neutral', icon: 'ok' };
  }
  if (key.includes('RASCUNHO') || key.includes('DRAFT')) {
    return { label: STATUS_LABELS.RASCUNHO, tone: 'neutral', icon: 'pendente' };
  }
  if (key.includes('CANCEL')) {
    return { label: STATUS_LABELS.CANCELADA, tone: 'danger', icon: 'erro' };
  }
  if (key.includes('DISPON') || key === 'LIVRE') {
    return { label: STATUS_LABELS.DISPONIVEL, tone: 'success', icon: 'ok' };
  }
  if (key.includes('OCUP')) {
    return { label: STATUS_LABELS.OCUPADO, tone: 'warning', icon: 'alerta' };
  }
  if (key.includes('CONFLITO') || key.includes('BLOQUE')) {
    return { label: STATUS_LABELS.CONFLITO, tone: 'danger', icon: 'erro' };
  }
  if (key.includes('ATEN') || key.includes('ALERT')) {
    return { label: STATUS_LABELS.ATENCAO, tone: 'warning', icon: 'alerta' };
  }
  if (key.includes('PEND')) {
    return { label: STATUS_LABELS.PENDENTE, tone: 'warning', icon: 'pendente' };
  }
  const label = String(raw ?? '').trim() || STATUS_LABELS.PENDENTE;
  return { label: label.toUpperCase(), tone: 'neutral', icon: 'pendente' };
}

type Props = {
  label?: string;
  /** Status bruto da API — resolve rótulo padronizado. */
  status?: string | null;
  icon?: keyof typeof ICONS | ReactNode;
  className?: string;
} & VariantProps<typeof statusBadgeVariants>;

/** Status com ícone + texto + cor (acessível, sem depender só da cor). */
export function StatusBadge({
  label,
  status,
  tone,
  icon,
  className,
}: Props) {
  const resolved = status != null ? resolveStatusPresentation(status) : null;
  const finalLabel = label ?? resolved?.label ?? STATUS_LABELS.PENDENTE;
  const finalTone = tone ?? resolved?.tone ?? 'neutral';
  const finalIcon = icon ?? resolved?.icon ?? 'pendente';

  const IconComp =
    typeof finalIcon === 'string' &&
    Object.prototype.hasOwnProperty.call(ICONS, finalIcon)
      ? ICONS[finalIcon as keyof typeof ICONS]
      : null;

  return (
    <span
      className={cn(statusBadgeVariants({ tone: finalTone }), className)}
      role="status"
    >
      {IconComp ? (
        <IconComp className="h-3.5 w-3.5 shrink-0" aria-hidden />
      ) : null}
      {typeof finalIcon !== 'string' ? finalIcon : null}
      <span>{finalLabel}</span>
    </span>
  );
}

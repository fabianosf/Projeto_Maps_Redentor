import type { ReactNode } from 'react';
import {
  AlertCircle,
  CheckCircle2,
  CircleDashed,
  Clock3,
  Bus,
  XCircle,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { resolveStatusPresentation } from '@/components/StatusBadge';

const TONE = {
  neutral: 'border-field bg-surface text-text',
  info: 'border-brand-cta/40 bg-brand-cta/10 text-brand-navy',
  success: 'border-ok/40 bg-ok/10 text-ok',
  warning: 'border-warn/40 bg-warn/10 text-warn',
  danger: 'border-danger/40 bg-danger/10 text-danger',
  primary: 'border-brand-navy/30 bg-brand-navy/10 text-brand-navy',
} as const;

const ICONS = {
  ok: CheckCircle2,
  erro: XCircle,
  alerta: AlertCircle,
  pendente: CircleDashed,
  tempo: Clock3,
  viagem: Bus,
} as const;

export type StatusSealTone = keyof typeof TONE;
export type StatusSealIcon = keyof typeof ICONS;

type Props = {
  label?: string;
  status?: string | null;
  tone?: StatusSealTone;
  icon?: StatusSealIcon | ReactNode;
  className?: string;
};

/** Selo de status: ícone + texto (não só cor). */
export function StatusSeal({
  label,
  status,
  tone,
  icon,
  className,
}: Props) {
  const resolved = status != null ? resolveStatusPresentation(status) : null;
  const finalLabel = label ?? resolved?.label ?? 'PENDENTE';
  const finalTone = (tone ?? resolved?.tone ?? 'neutral') as StatusSealTone;
  const mappedIcon =
    icon ??
    (resolved?.icon === 'tempo'
      ? 'tempo'
      : resolved?.icon === 'ok'
        ? 'ok'
        : resolved?.icon === 'erro'
          ? 'erro'
          : resolved?.icon === 'alerta'
            ? 'alerta'
            : 'pendente');

  const IconComp =
    typeof mappedIcon === 'string' && mappedIcon in ICONS
      ? ICONS[mappedIcon as StatusSealIcon]
      : null;

  return (
    <span
      className={cn(
        'inline-flex max-w-full items-center gap-1.5 rounded-xl border px-2.5 py-1 text-xs font-bold leading-tight uppercase tracking-wide',
        TONE[finalTone],
        className,
      )}
      role="status"
    >
      {IconComp ? (
        <IconComp className="h-3.5 w-3.5 shrink-0" aria-hidden />
      ) : typeof mappedIcon !== 'string' ? (
        mappedIcon
      ) : null}
      <span className="truncate">{finalLabel}</span>
    </span>
  );
}

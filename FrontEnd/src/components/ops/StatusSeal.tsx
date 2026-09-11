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

const TONE = {
  neutral: 'border-slate-200 bg-slate-100 text-slate-800',
  info: 'border-sky-200 bg-sky-50 text-sky-900',
  success: 'border-emerald-200 bg-emerald-50 text-emerald-900',
  warning: 'border-amber-200 bg-amber-50 text-amber-950',
  danger: 'border-red-200 bg-red-50 text-red-900',
  primary: 'border-primary/25 bg-primary/10 text-primary',
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
  label: string;
  tone?: StatusSealTone;
  icon?: StatusSealIcon | ReactNode;
  className?: string;
};

/** Selo de status: ícone + texto (não só cor). */
export function StatusSeal({
  label,
  tone = 'neutral',
  icon = 'pendente',
  className,
}: Props) {
  const IconComp =
    typeof icon === 'string' && icon in ICONS
      ? ICONS[icon as StatusSealIcon]
      : null;

  return (
    <span
      className={cn(
        'inline-flex max-w-full items-center gap-1 rounded-full border px-2 py-0.5 text-[11px] font-semibold leading-tight',
        TONE[tone],
        className,
      )}
      role="status"
    >
      {IconComp ? (
        <IconComp className="h-3 w-3 shrink-0" aria-hidden />
      ) : typeof icon !== 'string' ? (
        icon
      ) : null}
      <span className="truncate">{label}</span>
    </span>
  );
}

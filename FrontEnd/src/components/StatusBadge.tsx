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

const statusBadgeVariants = cva(
  'inline-flex items-center gap-1.5 rounded-md border px-2.5 py-1 text-xs font-semibold uppercase tracking-wide',
  {
    variants: {
      tone: {
        neutral:
          'border-slate-300 bg-slate-100 text-slate-800',
        info: 'border-sky-300 bg-sky-50 text-sky-900',
        success: 'border-emerald-300 bg-emerald-50 text-emerald-900',
        warning: 'border-amber-300 bg-amber-50 text-amber-950',
        danger: 'border-red-300 bg-red-50 text-red-900',
        primary: 'border-primary/30 bg-primary/10 text-primary',
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

type Props = {
  label: string;
  icon?: keyof typeof ICONS | ReactNode;
  className?: string;
} & VariantProps<typeof statusBadgeVariants>;

/** Status com ícone + texto + cor (acessível, sem depender só da cor). */
export function StatusBadge({ label, tone, icon = 'pendente', className }: Props) {
  const IconComp =
    typeof icon === 'string' && Object.prototype.hasOwnProperty.call(ICONS, icon)
      ? ICONS[icon as keyof typeof ICONS]
      : null;

  return (
    <span className={cn(statusBadgeVariants({ tone }), className)} role="status">
      {IconComp ? <IconComp className="h-3.5 w-3.5 shrink-0" aria-hidden /> : null}
      {typeof icon !== 'string' ? icon : null}
      <span>{label}</span>
    </span>
  );
}

import type { ReactNode } from 'react';
import { AlertTriangle, Info } from 'lucide-react';
import { cn } from '@/lib/utils';

type Tone = 'warning' | 'danger' | 'info';

type Props = {
  title: string;
  description?: string;
  tone?: Tone;
  action?: ReactNode;
  className?: string;
};

const TONE: Record<
  Tone,
  { wrap: string; icon: string; Icon: typeof AlertTriangle }
> = {
  warning: {
    wrap: 'border-amber-200 bg-amber-50',
    icon: 'text-amber-700',
    Icon: AlertTriangle,
  },
  danger: {
    wrap: 'border-red-200 bg-red-50',
    icon: 'text-red-600',
    Icon: AlertTriangle,
  },
  info: {
    wrap: 'border-sky-200 bg-sky-50',
    icon: 'text-sky-700',
    Icon: Info,
  },
};

/** Painel de alerta com ícone + texto (+ ação opcional). */
export function AlertPanel({
  title,
  description,
  tone = 'warning',
  action,
  className,
}: Props) {
  const t = TONE[tone];
  const Icon = t.Icon;
  return (
    <div
      className={cn(
        'flex items-start gap-3 rounded-2xl border px-3.5 py-3',
        t.wrap,
        className,
      )}
      role="alert"
    >
      <Icon className={cn('mt-0.5 h-5 w-5 shrink-0', t.icon)} aria-hidden />
      <div className="min-w-0 flex-1">
        <p className="text-sm font-bold text-slate-900">{title}</p>
        {description ? (
          <p className="mt-0.5 text-xs leading-snug text-slate-600">{description}</p>
        ) : null}
      </div>
      {action ? <div className="shrink-0 self-center">{action}</div> : null}
    </div>
  );
}

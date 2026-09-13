import type { ReactNode } from 'react';
import { AlertTriangle, Info, XCircle } from 'lucide-react';
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
    wrap: 'border-warn/40 bg-warn/10',
    icon: 'text-warn',
    Icon: AlertTriangle,
  },
  danger: {
    wrap: 'border-danger/40 bg-danger/10',
    icon: 'text-danger',
    Icon: XCircle,
  },
  info: {
    wrap: 'border-brand-cta/40 bg-brand-cta/10',
    icon: 'text-brand-navy',
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
        'flex items-start gap-3 rounded-xl border px-4 py-3.5',
        t.wrap,
        className,
      )}
      role="alert"
    >
      <Icon className={cn('mt-0.5 h-5 w-5 shrink-0', t.icon)} aria-hidden />
      <div className="min-w-0 flex-1">
        <p className="text-[15px] font-bold text-text">{title}</p>
        {description ? (
          <p className="mt-1 text-[14px] leading-snug text-text-muted">
            {description}
          </p>
        ) : null}
      </div>
      {action ? <div className="shrink-0 self-center">{action}</div> : null}
    </div>
  );
}

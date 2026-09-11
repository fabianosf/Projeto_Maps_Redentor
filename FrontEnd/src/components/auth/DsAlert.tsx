import type { ReactNode } from 'react';
import { AlertCircle, CheckCircle2, Info, TriangleAlert } from 'lucide-react';
import { cn } from '@/lib/utils';

type Tone = 'error' | 'success' | 'warning' | 'info';

type Props = {
  tone?: Tone;
  title?: string;
  children: ReactNode;
  className?: string;
};

const STYLES: Record<Tone, { wrap: string; icon: typeof Info }> = {
  error: {
    wrap: 'border-destructive/30 bg-destructive/5 text-destructive',
    icon: AlertCircle,
  },
  success: {
    wrap: 'border-success/30 bg-success/5 text-success',
    icon: CheckCircle2,
  },
  warning: {
    wrap: 'border-warning/30 bg-warning/5 text-warning',
    icon: TriangleAlert,
  },
  info: {
    wrap: 'border-info/30 bg-info/5 text-info',
    icon: Info,
  },
};

/** Alerta inline do design system (auth e hubs). */
export function DsAlert({ tone = 'info', title, children, className }: Props) {
  const s = STYLES[tone];
  const Icon = s.icon;
  return (
    <div
      role="alert"
      className={cn(
        'flex gap-3 rounded-xl border px-3.5 py-3 text-sm',
        s.wrap,
        className,
      )}
    >
      <Icon className="mt-0.5 h-5 w-5 shrink-0" aria-hidden />
      <div className="min-w-0 space-y-0.5 text-foreground">
        {title ? <p className="font-bold">{title}</p> : null}
        <div className="text-[13px] leading-snug text-foreground/90">{children}</div>
      </div>
    </div>
  );
}

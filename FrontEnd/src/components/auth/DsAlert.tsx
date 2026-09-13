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
    wrap: 'persistent-banner persistent-banner--error text-[15px]',
    icon: AlertCircle,
  },
  success: {
    wrap: 'persistent-banner persistent-banner--success text-[15px]',
    icon: CheckCircle2,
  },
  warning: {
    wrap: 'persistent-banner persistent-banner--warning text-[15px]',
    icon: TriangleAlert,
  },
  info: {
    wrap: 'persistent-banner persistent-banner--info text-[15px]',
    icon: Info,
  },
};

/** Alerta inline do design system (auth e hubs). */
export function DsAlert({ tone = 'info', title, children, className }: Props) {
  const s = STYLES[tone];
  const Icon = s.icon;
  return (
    <div role="alert" className={cn(s.wrap, className)}>
      <Icon className="mt-0.5 h-5 w-5 shrink-0" aria-hidden />
      <div className="min-w-0 space-y-0.5">
        {title ? <p className="font-bold">{title}</p> : null}
        <div className="text-[14px] font-medium leading-snug">{children}</div>
      </div>
    </div>
  );
}

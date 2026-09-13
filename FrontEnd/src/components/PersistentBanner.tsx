import type { ReactNode } from 'react';
import { AlertTriangle, CheckCircle2, Info, XCircle } from 'lucide-react';
import { cn } from '@/lib/utils';

type Tone = 'error' | 'warning' | 'info' | 'success';

type Props = {
  children: ReactNode;
  tone?: Tone;
  title?: string;
  className?: string;
  /** id para aria-describedby / live region */
  id?: string;
};

const TONE: Record<
  Tone,
  { wrap: string; Icon: typeof AlertTriangle; label: string }
> = {
  error: {
    wrap: 'persistent-banner persistent-banner--error',
    Icon: XCircle,
    label: 'Erro',
  },
  warning: {
    wrap: 'persistent-banner persistent-banner--warning',
    Icon: AlertTriangle,
    label: 'Aviso',
  },
  info: {
    wrap: 'persistent-banner persistent-banner--info',
    Icon: Info,
    label: 'Informação',
  },
  success: {
    wrap: 'persistent-banner persistent-banner--success',
    Icon: CheckCircle2,
    label: 'Sucesso',
  },
};

/** Banner persistente de erro/aviso/sucesso — legível por AT. */
export function PersistentBanner({
  children,
  tone = 'error',
  title,
  className,
  id,
}: Props) {
  const t = TONE[tone];
  const Icon = t.Icon;
  return (
    <div
      id={id}
      className={cn(t.wrap, className)}
      role="alert"
      aria-live="polite"
    >
      <Icon className="mt-0.5 h-5 w-5 shrink-0" aria-hidden />
      <div className="min-w-0 flex-1">
        {title ? <p className="font-bold">{title}</p> : null}
        <div className={cn(title ? 'mt-0.5 font-medium' : '', 'leading-snug')}>
          <span className="sr-only">{t.label}: </span>
          {children}
        </div>
      </div>
    </div>
  );
}

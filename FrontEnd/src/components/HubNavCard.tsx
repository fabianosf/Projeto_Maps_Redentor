import type { ReactNode } from 'react';
import { ChevronRight } from 'lucide-react';
import { cn } from '@/lib/utils';

type Props = {
  title: string;
  description?: string;
  icon: ReactNode;
  onClick: () => void;
  disabled?: boolean;
  meta?: ReactNode;
  className?: string;
  /** Destaque visual para ações prioritárias. */
  priority?: boolean;
};

/** Card de atalho grande — App de Campo Robusto. */
export function HubNavCard({
  title,
  description,
  icon,
  onClick,
  disabled,
  meta,
  className,
  priority,
}: Props) {
  return (
    <button
      type="button"
      disabled={disabled}
      onClick={onClick}
      className={cn(
        'flex w-full min-h-[5rem] items-center gap-3.5 rounded-xl border bg-surface-card px-4 py-4 text-left shadow-card transition-colors',
        priority ? 'border-brand-cta/50' : 'border-field',
        'hover:bg-surface active:bg-muted',
        'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring',
        'disabled:pointer-events-none disabled:opacity-50',
        className,
      )}
    >
      <span className="icon-circle-navy" aria-hidden>
        {icon}
      </span>
      <span className="min-w-0 flex-1">
        <span className="block text-base font-bold uppercase tracking-wide text-text">
          {title}
        </span>
        {description ? (
          <span className="mt-1 block text-[14px] leading-snug text-text-muted">
            {description}
          </span>
        ) : null}
        {meta ? <span className="mt-1.5 block">{meta}</span> : null}
      </span>
      <ChevronRight className="h-6 w-6 shrink-0 text-brand-cta" aria-hidden />
    </button>
  );
}

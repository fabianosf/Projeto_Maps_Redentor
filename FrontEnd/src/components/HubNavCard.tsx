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
};

/** Atalho em row: ícone circular navy + título + 1 linha. */
export function HubNavCard({
  title,
  description,
  icon,
  onClick,
  disabled,
  meta,
  className,
}: Props) {
  return (
    <button
      type="button"
      disabled={disabled}
      onClick={onClick}
      className={cn(
        'flex w-full min-h-[4.25rem] items-center gap-3 rounded-xl border border-border/60 bg-surface-card px-3.5 py-3 text-left shadow-sm transition-colors',
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
        <span className="block text-[15px] font-bold text-text">{title}</span>
        {description ? (
          <span className="mt-0.5 block text-[12px] leading-snug text-text-muted">
            {description}
          </span>
        ) : null}
        {meta ? <span className="mt-1.5 block">{meta}</span> : null}
      </span>
      <ChevronRight className="h-5 w-5 shrink-0 text-text-muted" aria-hidden />
    </button>
  );
}

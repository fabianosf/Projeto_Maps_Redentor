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

/** Card de hub (Registros / Mais / Início) — toque ≥ 44px. */
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
        'flex w-full min-h-[4.25rem] items-center gap-3 rounded-2xl border border-slate-200/90 bg-white px-3.5 py-3 text-left shadow-sm transition-colors',
        'hover:bg-slate-50 active:bg-slate-100',
        'disabled:pointer-events-none disabled:opacity-50',
        className,
      )}
    >
      <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-primary/10 text-primary">
        {icon}
      </span>
      <span className="min-w-0 flex-1">
        <span className="block text-[15px] font-bold text-slate-900">{title}</span>
        {description ? (
          <span className="mt-0.5 block text-[12px] leading-snug text-slate-600">
            {description}
          </span>
        ) : null}
        {meta ? <span className="mt-1.5 block">{meta}</span> : null}
      </span>
      <ChevronRight className="h-5 w-5 shrink-0 text-slate-400" aria-hidden />
    </button>
  );
}

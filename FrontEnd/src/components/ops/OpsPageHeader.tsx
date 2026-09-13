import type { ReactNode } from 'react';
import { ChevronLeft } from 'lucide-react';
import { cn } from '@/lib/utils';

type Props = {
  title: string;
  /** Telas internas: seta discreta. Abas principais da barra inferior: omitir. */
  onBack?: () => void;
  rightSlot?: ReactNode;
  className?: string;
};

/**
 * Cabeçalho operacional — navy #003B6F.
 */
export function OpsPageHeader({ title, onBack, rightSlot, className }: Props) {
  return (
    <header
      className={cn(
        'sticky top-0 z-20 flex h-14 shrink-0 items-center gap-0.5 bg-brand-navy px-1.5 text-primary-foreground shadow-sm',
        className,
      )}
    >
      {onBack ? (
        <button
          type="button"
          aria-label="Voltar"
          onClick={onBack}
          className={cn(
            'inline-flex h-12 w-12 min-h-[48px] min-w-[48px] shrink-0 items-center justify-center',
            'rounded-full border-0 bg-transparent p-0 text-primary-foreground shadow-none',
            'hover:bg-primary-foreground/10',
            'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-cta focus-visible:ring-offset-2 focus-visible:ring-offset-brand-navy',
          )}
        >
          <ChevronLeft className="h-6 w-6" strokeWidth={2.25} aria-hidden />
        </button>
      ) : (
        <span className="inline-block h-12 w-12 shrink-0" aria-hidden />
      )}
      <h1 className="flex-1 truncate text-center text-page-title uppercase tracking-wide">
        {title}
      </h1>
      <div className="flex h-12 min-h-[48px] min-w-12 shrink-0 items-center justify-end">
        {rightSlot ?? null}
      </div>
    </header>
  );
}

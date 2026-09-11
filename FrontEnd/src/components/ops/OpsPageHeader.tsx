import type { ReactNode } from 'react';
import { ChevronLeft } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

type Props = {
  title: string;
  onBack?: () => void;
  rightSlot?: ReactNode;
  className?: string;
};

/**
 * Cabeçalho azul institucional.
 * Voltar = ícone simples sem caixa/borda.
 */
export function OpsPageHeader({ title, onBack, rightSlot, className }: Props) {
  return (
    <header
      className={cn(
        'sticky top-0 z-20 flex h-14 shrink-0 items-center gap-0.5 bg-primary px-1.5 text-primary-foreground shadow-sm',
        className,
      )}
    >
      {onBack ? (
        <Button
          type="button"
          variant="ghost"
          size="icon"
          aria-label="Voltar"
          onClick={onBack}
          className="h-11 w-11 rounded-full text-primary-foreground hover:bg-primary-foreground/10"
        >
          <ChevronLeft className="h-6 w-6" strokeWidth={2.25} />
        </Button>
      ) : (
        <span className="w-11" aria-hidden />
      )}
      <h1 className="flex-1 truncate text-center text-page-title uppercase tracking-wide">
        {title}
      </h1>
      <div className="flex h-11 min-w-11 shrink-0 items-center justify-end">
        {rightSlot ?? null}
      </div>
    </header>
  );
}

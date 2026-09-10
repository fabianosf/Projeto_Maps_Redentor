import { Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';

type Props = {
  label?: string;
  className?: string;
};

export function LoadingState({ label = 'Carregando…', className }: Props) {
  return (
    <div
      className={cn(
        'flex flex-1 flex-col items-center justify-center gap-3 px-6 py-16 text-muted-foreground',
        className,
      )}
      role="status"
      aria-live="polite"
      aria-busy="true"
    >
      <Loader2 className="h-8 w-8 animate-spin text-primary" aria-hidden />
      <p className="text-sm font-semibold text-foreground/80">{label}</p>
      <p className="helper-text max-w-xs text-center">
        Aguarde enquanto os dados são carregados.
      </p>
    </div>
  );
}

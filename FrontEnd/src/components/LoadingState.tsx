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
    >
      <Loader2 className="h-8 w-8 animate-spin text-primary" aria-hidden />
      <p className="text-sm font-medium">{label}</p>
    </div>
  );
}

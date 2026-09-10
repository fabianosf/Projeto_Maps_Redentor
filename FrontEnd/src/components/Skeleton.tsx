import { cn } from '@/lib/utils';

type Props = {
  className?: string;
  /** Linhas de skeleton (lista/tabela). */
  rows?: number;
};

/** Placeholder de carregamento (sem spinner) para listas/tabelas. */
export function Skeleton({ className }: { className?: string }) {
  return (
    <div
      className={cn('animate-pulse rounded-md bg-slate-300/70', className)}
      aria-hidden
    />
  );
}

export function ListSkeleton({ className, rows = 5 }: Props) {
  return (
    <div
      className={cn('flex flex-col gap-3 p-4', className)}
      role="status"
      aria-live="polite"
      aria-label="Carregando"
    >
      {Array.from({ length: rows }).map((_, i) => (
        <div
          key={i}
          className="flex flex-col gap-2 rounded-xl border border-border/60 bg-card/70 p-4"
        >
          <Skeleton className="h-4 w-2/5" />
          <Skeleton className="h-3 w-4/5" />
          <Skeleton className="h-3 w-3/5" />
        </div>
      ))}
    </div>
  );
}

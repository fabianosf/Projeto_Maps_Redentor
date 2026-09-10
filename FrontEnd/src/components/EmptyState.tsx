import type { ReactNode } from 'react';
import { Inbox } from 'lucide-react';
import { cn } from '@/lib/utils';

type Props = {
  title?: string;
  description?: string;
  action?: ReactNode;
  className?: string;
};

export function EmptyState({
  title = 'Nenhum registro',
  description = 'Não há itens para exibir no momento.',
  action,
  className,
}: Props) {
  return (
    <div
      className={cn(
        'flex flex-1 flex-col items-center justify-center gap-3 rounded-xl border border-dashed border-border/80 bg-card/50 px-6 py-16 text-center',
        className,
      )}
      role="status"
    >
      <Inbox className="h-10 w-10 text-muted-foreground/60" aria-hidden />
      <div className="space-y-1">
        <p className="text-base font-semibold text-foreground">{title}</p>
        {description ? (
          <p className="helper-text mx-auto max-w-sm">{description}</p>
        ) : null}
      </div>
      {action}
    </div>
  );
}

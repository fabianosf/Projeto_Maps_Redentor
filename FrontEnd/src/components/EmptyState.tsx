import type { LucideIcon } from 'lucide-react';
import type { ReactNode } from 'react';
import { cn } from '@/lib/utils';

type Props = {
  title?: string;
  /** Uma frase objetiva. */
  description?: string;
  /** Ícone específico da tela — obrigatório evitar Inbox genérico em todas. */
  icon?: LucideIcon | ReactNode;
  action?: ReactNode;
  className?: string;
};

function isLucideIcon(icon: unknown): icon is LucideIcon {
  return typeof icon === 'function';
}

/**
 * Empty state: ícone + 1 frase + CTA.
 * Sempre passe `icon` contextual (MapPinned, UserPlus, ClipboardList…).
 */
export function EmptyState({
  title = 'Nenhum registro',
  description,
  icon,
  action,
  className,
}: Props) {
  const Icon = isLucideIcon(icon) ? icon : null;

  return (
    <div
      className={cn(
        'flex flex-1 flex-col items-center justify-center gap-3 rounded-xl border border-dashed border-border bg-surface-card px-6 py-16 text-center',
        className,
      )}
      role="status"
    >
      {Icon ? (
        <span className="icon-circle-navy" aria-hidden>
          <Icon className="h-5 w-5" strokeWidth={2.25} />
        </span>
      ) : icon ? (
        <span className="icon-circle-navy" aria-hidden>
          {icon}
        </span>
      ) : null}
      <div className="space-y-1">
        <p className="text-base font-semibold text-text">{title}</p>
        {description ? (
          <p className="helper-text mx-auto max-w-sm">{description}</p>
        ) : null}
      </div>
      {action}
    </div>
  );
}

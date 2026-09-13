import type { ReactNode, SyntheticEvent } from 'react';
import { cn } from '@/lib/utils';

type Props = {
  children: ReactNode;
  onClick?: () => void;
  className?: string;
  /** Faixa lateral de status (classe Tailwind bg-*). */
  stripeClass?: string;
  /** Ação primária textual — não dispara o onClick do card. */
  primaryAction?: ReactNode;
  'aria-label'?: string;
  disabled?: boolean;
  /** Destaque de seleção (borda azul espessa). */
  selected?: boolean;
};

/**
 * Card operacional clicável — App de Campo Robusto.
 */
export function OpsCard({
  children,
  onClick,
  className,
  stripeClass,
  primaryAction,
  'aria-label': ariaLabel,
  disabled,
  selected,
}: Props) {
  const stopAction = (e: SyntheticEvent) => {
    e.stopPropagation();
  };

  return (
    <div
      role={onClick ? 'button' : undefined}
      tabIndex={onClick && !disabled ? 0 : undefined}
      aria-label={ariaLabel}
      aria-disabled={disabled || undefined}
      aria-pressed={selected}
      onClick={disabled ? undefined : onClick}
      onKeyDown={
        onClick && !disabled
          ? (e) => {
              if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                onClick();
              }
            }
          : undefined
      }
      className={cn(
        'relative flex w-full overflow-hidden rounded-xl border bg-surface-card text-left text-text shadow-card outline-none transition-colors',
        selected ? 'border-[3px] border-brand-cta' : 'border-field',
        onClick &&
          !disabled &&
          'cursor-pointer active:bg-surface focus-visible:ring-2 focus-visible:ring-ring',
        disabled && 'opacity-60',
        className,
      )}
    >
      {stripeClass ? (
        <span className={cn('w-1.5 shrink-0 self-stretch', stripeClass)} aria-hidden />
      ) : null}
      <div className="flex min-w-0 flex-1 flex-col gap-2.5 px-4 py-3.5">
        {children}
        {primaryAction ? (
          <div className="pt-0.5" onClick={stopAction} onKeyDown={stopAction}>
            {primaryAction}
          </div>
        ) : null}
      </div>
    </div>
  );
}

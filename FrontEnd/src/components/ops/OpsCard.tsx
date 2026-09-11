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
};

/**
 * Card operacional clicável por inteiro, sem seta decorativa.
 * Feedback de toque via active:/focus-visible.
 */
export function OpsCard({
  children,
  onClick,
  className,
  stripeClass,
  primaryAction,
  'aria-label': ariaLabel,
  disabled,
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
        'relative flex w-full overflow-hidden rounded-2xl border border-slate-200/90 bg-white text-left shadow-sm outline-none transition-colors',
        onClick &&
          !disabled &&
          'cursor-pointer active:bg-slate-50 focus-visible:ring-2 focus-visible:ring-ring',
        disabled && 'opacity-60',
        className,
      )}
    >
      {stripeClass ? (
        <span className={cn('w-1.5 shrink-0 self-stretch', stripeClass)} aria-hidden />
      ) : null}
      <div className="flex min-w-0 flex-1 flex-col gap-2 px-3 py-2.5">
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

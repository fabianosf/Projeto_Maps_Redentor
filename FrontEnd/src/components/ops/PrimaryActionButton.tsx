import { forwardRef, type ButtonHTMLAttributes, type ReactNode } from 'react';
import { cn } from '@/lib/utils';

type Props = ButtonHTMLAttributes<HTMLButtonElement> & {
  children: ReactNode;
  loading?: boolean;
};

/** CTA operacional grande — cor de ação #006CC4. */
export const PrimaryActionButton = forwardRef<HTMLButtonElement, Props>(
  function PrimaryActionButton(
    { children, className, loading, disabled, ...rest },
    ref,
  ) {
    return (
      <button
        ref={ref}
        type="button"
        disabled={disabled || loading}
        className={cn(
          'inline-flex min-h-12 w-full items-center justify-center gap-2 rounded-xl bg-brand-cta px-4 text-base font-bold uppercase tracking-wide text-primary-foreground',
          'border border-brand-cta transition-colors hover:bg-brand-cta-deep active:bg-brand-cta-deep',
          'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2',
          'disabled:pointer-events-none disabled:opacity-60',
          className,
        )}
        {...rest}
      >
        {loading ? 'Salvando…' : children}
      </button>
    );
  },
);

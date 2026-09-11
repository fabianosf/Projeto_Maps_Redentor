import { forwardRef, type ButtonHTMLAttributes, type ReactNode } from 'react';
import { cn } from '@/lib/utils';

type Props = ButtonHTMLAttributes<HTMLButtonElement> & {
  children: ReactNode;
  fullWidth?: boolean;
};

/** Botão textual claro para a ação operacional principal do card. */
export const PrimaryActionButton = forwardRef<HTMLButtonElement, Props>(
  function PrimaryActionButton(
    { children, className, fullWidth = true, type = 'button', ...rest },
    ref,
  ) {
    return (
      <button
        ref={ref}
        type={type}
        className={cn(
          'inline-flex min-h-10 items-center justify-center rounded-xl bg-primary px-3 text-sm font-bold text-primary-foreground',
          'transition-colors hover:bg-primary/90 active:bg-primary/80',
          'disabled:pointer-events-none disabled:opacity-50',
          'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2',
          fullWidth ? 'w-full' : 'w-auto',
          className,
        )}
        {...rest}
      >
        {children}
      </button>
    );
  },
);

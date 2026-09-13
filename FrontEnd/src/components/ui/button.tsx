import * as React from 'react';
import { Slot } from '@radix-ui/react-slot';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '@/lib/utils';

const buttonVariants = cva(
  'inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-xl text-base font-bold uppercase tracking-wide transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-surface disabled:pointer-events-none disabled:opacity-60 [&_svg]:pointer-events-none [&_svg]:shrink-0',
  {
    variants: {
      variant: {
        default:
          'bg-brand-cta text-primary-foreground border border-brand-cta hover:bg-brand-cta-deep active:bg-brand-cta-deep',
        primary:
          'bg-brand-cta text-primary-foreground border border-brand-cta hover:bg-brand-cta-deep active:bg-brand-cta-deep',
        outline:
          'border-2 border-brand-navy bg-surface-card text-brand-navy hover:bg-surface',
        secondary:
          'bg-secondary text-secondary-foreground border border-field hover:bg-secondary/80',
        ghost: 'hover:bg-secondary text-brand-navy',
        destructive:
          'bg-danger text-primary-foreground hover:opacity-90',
        danger:
          'bg-danger text-primary-foreground hover:opacity-90',
        warning:
          'bg-warn text-primary-foreground border border-warn hover:opacity-90',
        toolbar:
          'flex-col gap-1.5 rounded-xl border border-brand-navy bg-brand-navy text-primary-foreground text-[11px] shadow-sm active:bg-brand-navy-deep',
      },
      size: {
        default: 'h-12 min-h-btn px-4',
        sm: 'h-12 min-h-12 px-3 text-sm',
        lg: 'h-14 min-h-14 px-6',
        icon: 'h-12 w-12 min-h-touch min-w-12',
        toolbar: 'h-[78px] min-h-[78px] w-full px-1 py-3',
        reset: 'h-[72px] w-[88px] flex-col gap-1 px-1 py-2 text-[12px]',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'default',
    },
  },
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean;
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : 'button';
    return (
      <Comp
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    );
  },
);
Button.displayName = 'Button';

export { Button, buttonVariants };

import * as React from 'react';
import { Slot } from '@radix-ui/react-slot';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '@/lib/utils';

const buttonVariants = cva(
  'inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-lg text-base font-bold uppercase tracking-wide transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-60 [&_svg]:pointer-events-none [&_svg]:shrink-0',
  {
    variants: {
      variant: {
        default:
          'bg-primary text-primary-foreground border border-primary hover:bg-primary/90 active:bg-primary/85',
        outline:
          'border border-primary bg-background text-primary hover:bg-secondary',
        secondary:
          'bg-secondary text-secondary-foreground hover:bg-secondary/80',
        ghost: 'hover:bg-secondary text-primary',
        destructive:
          'bg-destructive text-destructive-foreground hover:bg-destructive/90',
        toolbar:
          'flex-col gap-1.5 rounded-xl border border-primary bg-primary text-primary-foreground text-[11px] shadow-sm active:bg-primary/85',
      },
      size: {
        default: 'h-12 min-h-touch px-4',
        sm: 'h-10 min-h-10 px-3 text-sm',
        lg: 'h-14 min-h-14 px-6',
        icon: 'h-11 w-11 min-h-touch min-w-11',
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

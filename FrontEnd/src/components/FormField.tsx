import { forwardRef, type InputHTMLAttributes, type ReactNode } from 'react';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { cn } from '@/lib/utils';

type Props = InputHTMLAttributes<HTMLInputElement> & {
  label: string;
  requiredMark?: boolean;
  leftIcon?: ReactNode;
  rightSlot?: ReactNode;
  error?: string;
};

export const FormField = forwardRef<HTMLInputElement, Props>(function FormField(
  { label, requiredMark, leftIcon, rightSlot, error, id, className, ...rest },
  ref,
) {
  const inputId = id ?? rest.name ?? label.toLowerCase().replace(/\s+/g, '-');

  return (
    <div className="flex w-full flex-col gap-1.5">
      <Label
        htmlFor={inputId}
        className="flex h-5 items-center text-[15px] font-semibold uppercase leading-none text-slate-900"
      >
        {label.replace(/\s*\*$/, '')}
        {(requiredMark || label.includes('*')) && <span className="req"> *</span>}
      </Label>
      <div className="relative flex items-center">
        {leftIcon ? (
          <span className="pointer-events-none absolute left-3 z-[1] flex h-7 w-7 items-center justify-center rounded-full bg-muted text-muted-foreground">
            {leftIcon}
          </span>
        ) : null}
        <Input
          id={inputId}
          ref={ref}
          aria-invalid={error ? true : undefined}
          aria-describedby={error ? `${inputId}-error` : undefined}
          className={cn(
            'h-12 rounded-lg border-input bg-card text-base text-foreground shadow-none placeholder:text-muted-foreground/70',
            leftIcon && 'pl-12',
            rightSlot && 'pr-12',
            error && 'border-destructive focus-visible:ring-destructive',
            className,
          )}
          {...rest}
        />
        {rightSlot ? (
          <div className="absolute right-1 z-[1] flex items-center">{rightSlot}</div>
        ) : null}
      </div>
      {error ? (
        <span id={`${inputId}-error`} className="field-error" role="alert">
          {error}
        </span>
      ) : null}
    </div>
  );
});

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
  /** Rótulo em caixa alta (legado). Default: title case amigável. */
  labelUppercase?: boolean;
  hint?: string;
};

export const FormField = forwardRef<HTMLInputElement, Props>(function FormField(
  {
    label,
    requiredMark,
    leftIcon,
    rightSlot,
    error,
    hint,
    labelUppercase = false,
    id,
    className,
    ...rest
  },
  ref,
) {
  const inputId = id ?? rest.name ?? label.toLowerCase().replace(/\s+/g, '-');

  return (
    <div className="flex w-full flex-col gap-2">
      <Label
        htmlFor={inputId}
        className={cn(
          'flex min-h-5 items-center text-sm font-semibold leading-none text-foreground',
          labelUppercase && 'text-[15px] uppercase',
        )}
      >
        {label.replace(/\s*\*$/, '')}
        {(requiredMark || label.includes('*')) && <span className="req"> *</span>}
      </Label>
      <div className="relative flex items-center">
        {leftIcon ? (
          <span className="pointer-events-none absolute left-3 z-[1] flex h-8 w-8 items-center justify-center rounded-full bg-secondary text-primary">
            {leftIcon}
          </span>
        ) : null}
        <Input
          id={inputId}
          ref={ref}
          aria-invalid={error ? true : undefined}
          aria-describedby={
            error ? `${inputId}-error` : hint ? `${inputId}-hint` : undefined
          }
          className={cn(
            'h-12 min-h-touch rounded-xl border-input bg-card text-base text-foreground shadow-none placeholder:text-muted-foreground/70',
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
      ) : hint ? (
        <span id={`${inputId}-hint`} className="helper-text">
          {hint}
        </span>
      ) : null}
    </div>
  );
});

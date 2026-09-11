import { Check, Circle, X } from 'lucide-react';
import { cn } from '@/lib/utils';
import {
  forcaSenha,
  labelForcaSenha,
  requisitosSenha,
} from '@/utils/passwordStrength';

type Props = {
  password: string;
  className?: string;
};

const BAR: Record<0 | 1 | 2 | 3 | 4, string> = {
  0: 'bg-slate-200',
  1: 'bg-destructive',
  2: 'bg-warning',
  3: 'bg-info',
  4: 'bg-success',
};

/** Indicador de força + checklist em tempo real (não exibe a senha). */
export function PasswordStrength({ password, className }: Props) {
  const reqs = requisitosSenha(password);
  const score = forcaSenha(password);
  const filled = score;

  return (
    <div className={cn('space-y-3', className)} aria-live="polite">
      <div>
        <div className="mb-1.5 flex items-center justify-between gap-2">
          <span className="text-xs font-semibold text-muted-foreground">
            Força da senha
          </span>
          <span
            className={cn(
              'text-xs font-bold',
              score <= 1 && password
                ? 'text-destructive'
                : score === 2
                  ? 'text-warning'
                  : score >= 3
                    ? 'text-success'
                    : 'text-muted-foreground',
            )}
          >
            {password ? labelForcaSenha(score) : '—'}
          </span>
        </div>
        <div className="flex gap-1" aria-hidden>
          {[1, 2, 3, 4].map((i) => (
            <span
              key={i}
              className={cn(
                'h-1.5 flex-1 rounded-full transition-colors',
                i <= filled ? BAR[score] : 'bg-slate-200',
              )}
            />
          ))}
        </div>
      </div>

      <ul className="space-y-1.5" aria-label="Requisitos da senha">
        {reqs.map((r) => (
          <li key={r.id} className="flex items-center gap-2 text-[13px]">
            {password.length === 0 ? (
              <Circle className="h-3.5 w-3.5 shrink-0 text-slate-300" aria-hidden />
            ) : r.ok ? (
              <Check className="h-3.5 w-3.5 shrink-0 text-success" aria-hidden />
            ) : (
              <X className="h-3.5 w-3.5 shrink-0 text-destructive" aria-hidden />
            )}
            <span
              className={cn(
                r.ok && password.length > 0
                  ? 'font-medium text-success'
                  : 'text-muted-foreground',
              )}
            >
              {r.label}
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}

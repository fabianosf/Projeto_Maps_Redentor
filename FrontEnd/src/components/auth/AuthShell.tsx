import type { ReactNode } from 'react';
import { cn } from '@/lib/utils';
import { Logo } from '@/components/shared/Logo';
import { ui } from '@/theme/tokens';

type Props = {
  children: ReactNode;
  /** Título opcional sob a marca. */
  title?: string;
  subtitle?: string;
  className?: string;
};

/**
 * Shell de autenticação — sem barra inferior / sem menu.
 * Fundo claro institucional.
 */
export function AuthShell({ children, title, subtitle, className }: Props) {
  return (
    <div
      className={cn(
        'auth-shell mx-auto flex min-h-dvh w-full max-w-phone flex-col',
        className,
      )}
    >
      <div className="auth-shell-bg pointer-events-none absolute inset-0" aria-hidden />
      <div className="relative z-[1] flex min-h-dvh flex-col px-5 py-8 sm:px-6">
        <header className="mb-6 flex flex-col items-center text-center">
          <Logo compact />
          <p className="-mt-1 text-xl font-bold tracking-tight text-primary">
            RedMapa
          </p>
          {title ? (
            <h1 className="mt-4 text-lg font-bold text-foreground">{title}</h1>
          ) : null}
          {subtitle ? (
            <p className={cn(ui.helper, 'mt-1 max-w-[20rem]')}>{subtitle}</p>
          ) : null}
        </header>
        <main className="mx-auto flex w-full max-w-[360px] flex-1 flex-col">
          {children}
        </main>
      </div>
    </div>
  );
}

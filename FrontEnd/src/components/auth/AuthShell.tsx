import type { CSSProperties, ReactNode } from 'react';
import { cn } from '@/lib/utils';
import { Logo } from '@/components/shared/Logo';
import { LoginBusIcon } from '@/components/auth/LoginBusIcon';
import authBgInstitucional from '@/assets/auth-bg-institucional.png';

type Props = {
  children: ReactNode;
  title?: string;
  subtitle?: string;
  className?: string;
  /** /login: marca circular + tipografia do mockup. */
  loginMark?: boolean;
};

/**
 * Shell de autenticação — navy + poster fantasma.
 * Só telas auth (não usar em AppShell logado).
 */
export function AuthShell({
  children,
  title,
  subtitle,
  className,
  loginMark = false,
}: Props) {
  const bgStyle = {
    ['--auth-bg-image' as string]: `url(${authBgInstitucional})`,
  } as CSSProperties;

  return (
    <div
      className={cn(
        'auth-shell mx-auto flex min-h-dvh w-full max-w-phone flex-col',
        className,
      )}
    >
      <div
        className="auth-shell-bg pointer-events-none absolute inset-0"
        style={bgStyle}
        aria-hidden
      />
      <div
        className={cn(
          'relative z-[1] flex min-h-dvh flex-col px-5 py-8 sm:px-6',
          loginMark && 'justify-center',
        )}
      >
        <header
          className={cn(
            'mb-6 flex flex-col items-center text-center',
            loginMark && 'mb-8',
          )}
        >
          {loginMark ? (
            <>
              <div className="login-mark" aria-hidden>
                <span className="login-mark-inner">
                  <LoginBusIcon className="login-mark-bus" />
                </span>
              </div>
              <h1 className="login-brand-title">RedMapa</h1>
              <p className="login-brand-org">Grupo Redentor</p>
            </>
          ) : (
            <>
              <Logo compact />
              <p className="text-xl font-bold tracking-tight text-primary-foreground">
                RedMapa
              </p>
              <p className="mt-0.5 text-sm font-medium text-brand-cyan">
                Grupo Redentor
              </p>
            </>
          )}
          {title ? (
            <h2 className="mt-4 text-lg font-bold text-primary-foreground">{title}</h2>
          ) : null}
          {subtitle ? (
            <p
              className={cn(
                'mt-1 max-w-[20rem] text-sm leading-snug text-white/85',
                loginMark && 'mt-2.5',
              )}
            >
              {subtitle}
            </p>
          ) : null}
        </header>
        <main className="mx-auto flex w-full max-w-[360px] flex-col">
          {children}
        </main>
      </div>
    </div>
  );
}

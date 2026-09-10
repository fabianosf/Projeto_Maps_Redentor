import type { ReactNode } from 'react';
import { AppShell } from '@/components/AppShell';
import { PageHeader } from '@/components/PageHeader';
import { useScreenBg } from '@/hooks/useScreenBg';
import { SCREEN_BG } from '@/theme/tokens';
import { cn } from '@/lib/utils';

type Props = {
  title: string;
  onBack?: () => void;
  rightSlot?: ReactNode;
  children: ReactNode;
  className?: string;
  bodyClassName?: string;
  /** Cor de fundo da tela (padrão corporativo). */
  bg?: string;
};

/**
 * Layout padrão de página: AppShell + PageHeader + fundo consistente.
 * Não altera rotas/permissões — só estrutura visual.
 */
export function PageLayout({
  title,
  onBack,
  rightSlot,
  children,
  className,
  bodyClassName,
  bg = SCREEN_BG,
}: Props) {
  useScreenBg(bg);

  return (
    <AppShell className={cn('bg-screen', className)}>
      <div className="page flex min-h-dvh flex-col bg-screen text-foreground">
        <PageHeader title={title} onBack={onBack} rightSlot={rightSlot} />
        <div className={cn('page-body bg-screen', bodyClassName)}>{children}</div>
      </div>
    </AppShell>
  );
}

import type { ReactNode } from 'react';
import { useNavigate } from 'react-router-dom';
import { AppShell } from '@/components/AppShell';
import { PageHeader } from '@/components/PageHeader';

type Props = {
  title: string;
  showBack?: boolean;
  children?: ReactNode;
};

/** Placeholder de rota — telas de negócio virão depois. */
export function PlaceholderPage({ title, showBack = true, children }: Props) {
  const navigate = useNavigate();

  return (
    <AppShell>
      <div className="page">
        <PageHeader
          title={title}
          onBack={showBack ? () => navigate(-1) : undefined}
        />
        <div className="page-body-center">
          {children ?? (
            <p className="max-w-sm text-center text-sm text-muted-foreground">
              Fundação do frontend — tela de negócio ainda não implementada.
            </p>
          )}
        </div>
      </div>
    </AppShell>
  );
}

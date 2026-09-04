import { Navigate } from 'react-router-dom';
import { AppShell } from '@/components/AppShell';
import { LoadingState } from '@/components/LoadingState';
import { PageHeader } from '@/components/PageHeader';
import { useAuth } from '@/context/AuthContext';

/** Placeholder público de login (sem formulário de negócio ainda). */
export function LoginPage() {
  const { user, loading } = useAuth();

  if (loading) return <LoadingState />;
  if (user) return <Navigate to="/principal" replace />;

  return (
    <AppShell>
      <div className="page">
        <PageHeader title="Login" />
        <div className="page-body-center">
          <p className="max-w-sm text-center text-sm text-muted-foreground">
            Fundação do frontend — formulário de login será implementado em seguida.
          </p>
        </div>
      </div>
    </AppShell>
  );
}

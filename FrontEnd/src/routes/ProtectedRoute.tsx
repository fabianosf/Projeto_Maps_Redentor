import { Navigate, Outlet, useLocation } from 'react-router-dom';
import { LoadingState } from '@/components/LoadingState';
import { useAuth } from '@/context/AuthContext';

/** Rotas filhas exigem sessão; caso contrário redireciona para /login. */
export function ProtectedRoute() {
  const { user, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    return <LoadingState label="Verificando sessão…" />;
  }

  if (!user) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  }

  return <Outlet />;
}

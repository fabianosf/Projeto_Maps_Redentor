import { PlaceholderPage } from '@/pages/PlaceholderPage';
import { useAuth } from '@/context/AuthContext';

export function PrincipalPage() {
  const { user } = useAuth();
  return (
    <PlaceholderPage title="Principal" showBack={false}>
      <p className="max-w-sm text-center text-sm text-muted-foreground">
        Olá, {user?.nome ?? 'usuário'} ({user?.matricula}). Fundação — menu principal em
        seguida.
      </p>
    </PlaceholderPage>
  );
}

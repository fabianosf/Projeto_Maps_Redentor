import { useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { BarChart3, Cog, LogOut, UserCog, UserRound } from 'lucide-react';
import { AppShell } from '@/components/AppShell';
import { HubNavCard } from '@/components/HubNavCard';
import { PageHeader } from '@/components/PageHeader';
import { StatusBadge } from '@/components/StatusBadge';
import { useAuth } from '@/context/AuthContext';
import { useScreenBg } from '@/hooks/useScreenBg';
import { AUTH_BG } from '@/theme/tokens';
import {
  canAccessCadastroUsuario,
  canAccessConfiguracao,
} from '@/utils/perfilAccess';

/**
 * Hub Mais — cadastros, configurações e perfil.
 */
export function MaisScreen() {
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  useScreenBg(AUTH_BG);

  const podeConfig = canAccessConfiguracao(user?.codigo_perfil);
  const podeUsuarios = canAccessCadastroUsuario(user?.codigo_perfil);

  const handleSair = useCallback(() => {
    void logout();
  }, [logout]);

  return (
    <AppShell className="bg-background">
      <div className="page flex min-h-dvh flex-col bg-background text-foreground">
        <PageHeader title="Mais" />

        <div className="page-body flex-1 gap-4 pb-tabbar">
          <section className="surface-card rounded-2xl px-4 py-3.5">
            <div className="flex items-center gap-3">
              <span className="flex h-12 w-12 items-center justify-center rounded-full bg-primary text-sm font-bold text-primary-foreground">
                <UserRound className="h-6 w-6" aria-hidden />
              </span>
              <div className="min-w-0">
                <h2 className="truncate text-base font-bold text-slate-900">
                  {user?.nome ?? 'Usuário'}
                </h2>
                <p className="text-sm text-slate-600">
                  Matrícula {user?.matricula ?? '—'}
                </p>
              </div>
            </div>
            <div className="mt-3">
              <StatusBadge label="Perfil autenticado" tone="success" icon="ok" />
            </div>
          </section>

          <nav className="flex flex-col gap-2.5" aria-label="Cadastros e configurações">
            {podeConfig ? (
              <HubNavCard
                title="Configuração"
                description="Tentativas de login e parâmetros"
                icon={<Cog className="h-5 w-5" aria-hidden />}
                onClick={() => navigate('/configuracao')}
              />
            ) : null}
            {podeUsuarios ? (
              <HubNavCard
                title="Usuários"
                description="Cadastro e permissões"
                icon={<UserCog className="h-5 w-5" aria-hidden />}
                onClick={() => navigate('/usuarios')}
              />
            ) : null}
            {podeConfig ? (
              <HubNavCard
                title="Indicadores (config)"
                description="Cadastro de indicadores do painel"
                icon={<BarChart3 className="h-5 w-5" aria-hidden />}
                onClick={() => navigate('/configuracao/indicadores')}
              />
            ) : null}
            <HubNavCard
              title="Sair"
              description="Encerrar sessão neste dispositivo"
              icon={<LogOut className="h-5 w-5" aria-hidden />}
              onClick={handleSair}
              className="border-red-200/80"
            />
          </nav>

          {!podeConfig ? (
            <p className="helper-text px-1">
              Cadastros e configuração estão disponíveis para Administrador e
              Inspetor.
            </p>
          ) : null}
        </div>
      </div>
    </AppShell>
  );
}

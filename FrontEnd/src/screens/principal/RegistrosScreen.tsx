import { useNavigate } from 'react-router-dom';
import { BarChart3, Bus, Clock3 } from 'lucide-react';
import { AppShell } from '@/components/AppShell';
import { HubNavCard } from '@/components/HubNavCard';
import { PageHeader } from '@/components/PageHeader';
import { StatusBadge } from '@/components/StatusBadge';
import { useAuth } from '@/context/AuthContext';
import { useScreenBg } from '@/hooks/useScreenBg';
import { SCREEN_BG } from '@/theme/tokens';
import { canAccessBancoHoras } from '@/utils/perfilAccess';

/**
 * Hub Registros — histórico operacional, ajustes e auditoria.
 * Não altera regras de negócio das telas destino.
 */
export function RegistrosScreen() {
  const navigate = useNavigate();
  const { user } = useAuth();
  useScreenBg(SCREEN_BG);

  const podeBancoHoras = canAccessBancoHoras(user?.codigo_perfil);

  return (
    <AppShell className="bg-screen">
      <div className="page flex min-h-dvh flex-col bg-screen text-slate-900">
        <PageHeader title="Registros" />

        <div className="page-body flex-1 gap-4 pb-tabbar">
          <section className="surface-card rounded-2xl px-4 py-3.5">
            <h2 className="text-base font-bold text-slate-900">
              Histórico e auditoria
            </h2>
            <p className="mt-1 text-sm leading-snug text-slate-600">
              Consulte chegadas/saídas, jornadas e indicadores. Ajustes e
              conferências ficam nestes módulos.
            </p>
            <div className="mt-3">
              <StatusBadge label="Somente consulta e registro" tone="neutral" icon="pendente" />
            </div>
          </section>

          <nav className="flex flex-col gap-2.5" aria-label="Módulos de registros">
            <HubNavCard
              title="Chegada / Saída"
              description="Registros de entrada e saída de veículos"
              icon={<Bus className="h-5 w-5" aria-hidden />}
              onClick={() => navigate('/entrada-saida')}
            />
            {podeBancoHoras ? (
              <HubNavCard
                title="Banco de horas"
                description="Jornada, baixa e ajustes operacionais"
                icon={<Clock3 className="h-5 w-5" aria-hidden />}
                onClick={() => navigate('/banco-horas')}
              />
            ) : null}
            <HubNavCard
              title="Indicadores"
              description="Painel e acompanhamento"
              icon={<BarChart3 className="h-5 w-5" aria-hidden />}
              onClick={() => navigate('/indicadores')}
            />
          </nav>
        </div>
      </div>
    </AppShell>
  );
}

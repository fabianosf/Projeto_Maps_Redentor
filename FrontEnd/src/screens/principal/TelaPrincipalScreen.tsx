import { useNavigate } from 'react-router-dom';
import {
  AlertTriangle,
  BarChart3,
  Bus,
  Clock3,
  MapPinned,
  NotebookTabs,
} from 'lucide-react';
import { AppShell } from '@/components/AppShell';
import { HubNavCard } from '@/components/HubNavCard';
import { PageHeader } from '@/components/PageHeader';
import { StatusBadge } from '@/components/StatusBadge';
import { useAuth } from '@/context/AuthContext';
import { useScreenBg } from '@/hooks/useScreenBg';
import { SCREEN_BG } from '@/theme/tokens';
import {
  canAccessBancoHoras,
  canAccessMapas,
} from '@/utils/perfilAccess';

function formatHoje(): string {
  try {
    return new Intl.DateTimeFormat('pt-BR', {
      weekday: 'long',
      day: '2-digit',
      month: 'long',
    }).format(new Date());
  } catch {
    return new Date().toLocaleDateString('pt-BR');
  }
}

/** Início — resumo operacional do dia e atalhos (sem menu legado). */
export function TelaPrincipalScreen() {
  const navigate = useNavigate();
  const { user } = useAuth();
  useScreenBg(SCREEN_BG);

  const podeMapas = canAccessMapas(user?.codigo_perfil);
  const podeBancoHoras = canAccessBancoHoras(user?.codigo_perfil);

  return (
    <AppShell className="bg-screen">
      <div className="page box-border flex min-h-dvh flex-col bg-screen text-slate-900">
        <PageHeader title="Início" />

        <div className="page-body flex-1 gap-4 pb-tabbar">
          <section className="surface-card rounded-2xl px-4 py-3.5">
            <p className="text-[11px] font-semibold uppercase tracking-wide text-primary">
              Resumo do dia
            </p>
            <h2 className="mt-1 text-lg font-bold capitalize leading-snug text-slate-900">
              {formatHoje()}
            </h2>
            {user ? (
              <p className="mt-1 text-sm text-slate-600">
                {user.nome}
                <span className="text-slate-400"> · </span>
                Matrícula {user.matricula}
              </p>
            ) : null}
            <div className="mt-3 flex flex-wrap gap-2">
              <StatusBadge label="Sessão ativa" tone="success" icon="ok" />
              <StatusBadge label="Operação do dia" tone="info" icon="tempo" />
            </div>
          </section>

          <section className="space-y-2" aria-label="Alertas">
            <h3 className="px-0.5 text-[13px] font-bold uppercase tracking-wide text-slate-700">
              Alertas
            </h3>
            <div className="flex items-start gap-3 rounded-2xl border border-amber-200 bg-amber-50 px-3.5 py-3">
              <AlertTriangle
                className="mt-0.5 h-5 w-5 shrink-0 text-amber-700"
                aria-hidden
              />
              <div className="min-w-0">
                <p className="text-sm font-bold text-amber-950">
                  Acompanhe pendências na Guia
                </p>
                <p className="mt-0.5 text-xs leading-snug text-amber-900/80">
                  Saídas, chegadas, leituras e divergências ficam no módulo
                  operacional Guia.
                </p>
              </div>
            </div>
          </section>

          <section className="space-y-2" aria-label="Atalhos operacionais">
            <h3 className="px-0.5 text-[13px] font-bold uppercase tracking-wide text-slate-700">
              Atalhos
            </h3>
            <div className="flex flex-col gap-2.5">
              {podeMapas ? (
                <HubNavCard
                  title="Mapas"
                  description="Planejamento de escalas do turno"
                  icon={<MapPinned className="h-5 w-5" aria-hidden />}
                  onClick={() => navigate('/mapas')}
                />
              ) : null}
              <HubNavCard
                title="Guia"
                description="Registrar e acompanhar viagens"
                icon={<NotebookTabs className="h-5 w-5" aria-hidden />}
                onClick={() => navigate('/guia')}
                meta={
                  <StatusBadge label="Operacional" tone="primary" icon="tempo" />
                }
              />
              <HubNavCard
                title="Chegada / Saída"
                description="Registros de ponto e auditoria"
                icon={<Bus className="h-5 w-5" aria-hidden />}
                onClick={() => navigate('/entrada-saida')}
              />
              {podeBancoHoras ? (
                <HubNavCard
                  title="Banco de horas"
                  description="Histórico e ajustes de jornada"
                  icon={<Clock3 className="h-5 w-5" aria-hidden />}
                  onClick={() => navigate('/banco-horas')}
                />
              ) : null}
              <HubNavCard
                title="Indicadores"
                description="Painel operacional"
                icon={<BarChart3 className="h-5 w-5" aria-hidden />}
                onClick={() => navigate('/indicadores')}
              />
            </div>
          </section>
        </div>
      </div>
    </AppShell>
  );
}

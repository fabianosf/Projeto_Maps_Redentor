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
import { AppHeader } from '@/components/AppHeader';
import { HubNavCard } from '@/components/HubNavCard';
import { Card, CardContent } from '@/components/ui/card';
import { Pill } from '@/components/ui/pill';
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

/** Início — resumo do dia + atalhos (sem menu legado). */
export function TelaPrincipalScreen() {
  const navigate = useNavigate();
  const { user } = useAuth();
  useScreenBg(SCREEN_BG);

  const podeMapas = canAccessMapas(user?.codigo_perfil);
  const podeBancoHoras = canAccessBancoHoras(user?.codigo_perfil);

  return (
    <AppShell className="bg-surface">
      <div className="page box-border flex min-h-dvh flex-col bg-surface text-text">
        <AppHeader title="Início" />

        <div className="page-body flex-1 gap-4 pb-tabbar">
          <Card filletGold>
            <CardContent className="space-y-3 p-4">
              <p className="text-[11px] font-semibold uppercase tracking-wide text-brand-navy">
                Resumo do dia
              </p>
              <h2 className="text-lg font-bold capitalize leading-snug text-text">
                {formatHoje()}
              </h2>
              {user ? (
                <p className="text-sm text-text-muted">
                  {user.nome}
                  <span className="text-text-muted/60"> · </span>
                  Matrícula {user.matricula}
                </p>
              ) : null}
              <div className="flex flex-wrap gap-2">
                <Pill label="Sessão ativa" tone="ok" />
                <Pill label="Operação do dia" tone="info" />
              </div>
            </CardContent>
          </Card>

          <section className="space-y-2" aria-label="Alertas">
            <h3 className="px-0.5 text-[13px] font-bold uppercase tracking-wide text-text">
              Alertas
            </h3>
            <div className="flex items-start gap-3 rounded-xl border border-brand-gold/35 bg-brand-gold/10 px-3.5 py-3">
              <AlertTriangle
                className="mt-0.5 h-5 w-5 shrink-0 text-brand-gold"
                aria-hidden
              />
              <div className="min-w-0">
                <p className="text-sm font-bold text-text">
                  Acompanhe pendências na Guia
                </p>
                <p className="mt-0.5 text-xs leading-snug text-text-muted">
                  Saídas, chegadas, leituras e divergências ficam no módulo
                  operacional Guia.
                </p>
              </div>
            </div>
          </section>

          <section className="space-y-2" aria-label="Atalhos operacionais">
            <h3 className="px-0.5 text-[13px] font-bold uppercase tracking-wide text-text">
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

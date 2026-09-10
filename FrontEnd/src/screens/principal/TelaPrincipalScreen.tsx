import { useCallback, type ReactNode } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  BarChart3,
  Clock3,
  Cog,
  LogOut,
  Map,
  MapPinned,
  NotebookTabs,
} from 'lucide-react';
import { AppShell } from '@/components/AppShell';
import { PageHeader } from '@/components/PageHeader';
import { Button } from '@/components/ui/button';
import { useAuth } from '@/context/AuthContext';
import { useScreenBg } from '@/hooks/useScreenBg';
import { actionBtn3dBase } from '@/lib/actionBtn3d';
import { cn } from '@/lib/utils';
import { SCREEN_BG } from '@/theme/tokens';
import {
  canAccessBancoHoras,
  canAccessConfiguracao,
  canAccessMapas,
} from '@/utils/perfilAccess';

const BG = SCREEN_BG;

/** Cards grandes — área de toque ≥ 44px (WCAG / mobile). */
const cardBtnClass = cn(
  actionBtn3dBase,
  'flex h-14 min-h-[44px] w-full max-w-[320px] items-center justify-center gap-2 px-4 text-[15px]',
);

type MenuCard = {
  id: string;
  label: string;
  ariaLabel: string;
  icon: ReactNode;
  onClick: () => void;
};

export function TelaPrincipalScreen() {
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  useScreenBg(BG);

  const podeConfiguracao = canAccessConfiguracao(user?.codigo_perfil);
  const podeMapas = canAccessMapas(user?.codigo_perfil);
  const podeBancoHoras = canAccessBancoHoras(user?.codigo_perfil);

  const handleSair = useCallback(() => {
    void logout();
  }, [logout]);

  const cards: MenuCard[] = [];

  if (podeMapas) {
    cards.push({
      id: 'mapas',
      label: 'MAPAS',
      ariaLabel: 'Mapas',
      icon: <MapPinned className="h-5 w-5 shrink-0" strokeWidth={2.25} aria-hidden />,
      onClick: () => navigate('/mapas'),
    });
  }

  if (podeBancoHoras) {
    cards.push({
      id: 'banco-horas',
      label: 'Banco de horas',
      ariaLabel: 'Banco de horas operacional',
      icon: <Clock3 className="h-5 w-5 shrink-0" strokeWidth={2.25} aria-hidden />,
      onClick: () => navigate('/banco-horas'),
    });
  }

  cards.push(
    {
      id: 'guia',
      label: 'Guia',
      ariaLabel: 'Guia',
      icon: <NotebookTabs className="h-5 w-5 shrink-0" strokeWidth={2.25} aria-hidden />,
      onClick: () => navigate('/guia'),
    },
    {
      id: 'entrada-saida',
      label: 'Chegada / Saída',
      ariaLabel: 'Chegada e Saída',
      icon: <Map className="h-5 w-5 shrink-0" strokeWidth={2.25} aria-hidden />,
      onClick: () => navigate('/entrada-saida'),
    },
    {
      id: 'indicadores',
      label: 'Indicadores',
      ariaLabel: 'Indicadores',
      icon: <BarChart3 className="h-5 w-5 shrink-0" strokeWidth={2.25} aria-hidden />,
      onClick: () => navigate('/indicadores'),
    },
  );

  if (podeConfiguracao) {
    cards.push({
      id: 'configuracao',
      label: 'Configuração',
      ariaLabel: 'Configuração',
      icon: <Cog className="h-5 w-5 shrink-0" strokeWidth={2.25} aria-hidden />,
      onClick: () => navigate('/configuracao'),
    });
  }

  cards.push({
    id: 'sair',
    label: 'Sair',
    ariaLabel: 'Sair',
    icon: <LogOut className="h-5 w-5 shrink-0" strokeWidth={2.25} aria-hidden />,
    onClick: handleSair,
  });

  return (
    <AppShell className="bg-screen">
      <div className="page box-border flex min-h-dvh flex-col bg-screen text-slate-900">
        <PageHeader title="RedMapa" />

        <div className="page-body-center flex-1 gap-3 py-6">
          {user ? (
            <div className="surface-card mb-2 w-full max-w-[320px] px-4 py-3 text-center">
              <p className="text-sm font-semibold text-foreground">{user.nome}</p>
              <p className="helper-text mt-0.5">Matrícula {user.matricula}</p>
            </div>
          ) : null}

          <nav
            className="flex w-full max-w-[320px] flex-col items-center gap-3"
            aria-label="Menu principal"
          >
            {cards.map((card) => (
              <Button
                key={card.id}
                type="button"
                className={cardBtnClass}
                aria-label={card.ariaLabel}
                onClick={card.onClick}
              >
                {card.icon}
                <span>{card.label}</span>
              </Button>
            ))}
          </nav>
        </div>
      </div>
    </AppShell>
  );
}

import { useEffect, useRef, useState } from 'react';
import {
  Route,
  Routes,
  useLocation,
  useNavigate,
  type Location,
} from 'react-router-dom';
import { BottomTabBar } from '@/components/BottomTabBar';
import {
  MAIN_TABS,
  defaultPathForTab,
  resolveMainTab,
  type MainTabId,
} from '@/navigation/mainTabs';
import { cn } from '@/lib/utils';
import { UsuariosScreen } from '@/screens/admin/UsuariosScreen';
import { MapasListScreen } from '@/screens/mapa/MapasListScreen';
import { MapaDetalheScreen } from '@/screens/mapa/MapaDetalheScreen';
import { MapaFormScreen } from '@/screens/mapa/MapaFormScreen';
import { BancoHorasScreen } from '@/screens/principal/BancoHorasScreen';
import { ConfiguracaoScreen } from '@/screens/principal/ConfiguracaoScreen';
import { EntradaSaidaScreen } from '@/screens/principal/EntradaSaidaScreen';
import { GuiaScreen } from '@/screens/principal/GuiaScreen';
import { IndicadoresConfigScreen } from '@/screens/principal/IndicadoresConfigScreen';
import { IndicadoresScreen } from '@/screens/principal/IndicadoresScreen';
import { MaisScreen } from '@/screens/principal/MaisScreen';
import { NovaGuiaScreen } from '@/screens/principal/NovaGuiaScreen';
import { RegistrosScreen } from '@/screens/principal/RegistrosScreen';
import { TelaPrincipalScreen } from '@/screens/principal/TelaPrincipalScreen';

function stubLocation(pathname: string): Location {
  return {
    pathname,
    search: '',
    hash: '',
    state: null,
    key: `tab:${pathname}`,
  };
}

/**
 * Layout autenticado com barra inferior e painéis keep-alive por aba.
 * Trocar de aba não desmonta o painel — preserva formulários e contexto.
 */
export function MainTabLayout() {
  const location = useLocation();
  const navigate = useNavigate();
  const activeTab = resolveMainTab(location.pathname);

  const lastByTab = useRef<Partial<Record<MainTabId, Location>>>({
    inicio: stubLocation('/principal'),
    mapas: stubLocation('/mapas'),
    guia: stubLocation('/guia'),
    registros: stubLocation('/registros'),
    mais: stubLocation('/mais'),
  });

  const [visited, setVisited] = useState<Set<MainTabId>>(
    () => new Set<MainTabId>([activeTab]),
  );

  useEffect(() => {
    lastByTab.current[activeTab] = location;
    setVisited((prev) => {
      if (prev.has(activeTab)) return prev;
      const next = new Set(prev);
      next.add(activeTab);
      return next;
    });
  }, [activeTab, location]);

  useEffect(() => {
    const matched = MAIN_TABS.some((t) => t.match(location.pathname));
    if (!matched) {
      navigate('/principal', { replace: true });
    }
  }, [location.pathname, navigate]);

  const onSelectTab = (tabId: MainTabId) => {
    if (tabId === activeTab) {
      // Segundo toque na aba ativa: volta à raiz do módulo
      const root = defaultPathForTab(tabId);
      if (location.pathname !== root) navigate(root);
      return;
    }
    const saved = lastByTab.current[tabId];
    navigate(saved ? `${saved.pathname}${saved.search}` : defaultPathForTab(tabId));
  };

  return (
    <div className="relative mx-auto flex min-h-dvh w-full max-w-phone flex-col bg-screen">
      <div className="relative flex min-h-0 flex-1 flex-col">
        {MAIN_TABS.map((tab) => {
          if (!visited.has(tab.id)) return null;
          const loc =
            tab.id === activeTab
              ? location
              : (lastByTab.current[tab.id] ?? stubLocation(tab.path));
          const isActive = tab.id === activeTab;
          return (
            <div
              key={tab.id}
              className={cn(
                'main-tab-panel min-h-0 flex-1 flex-col',
                isActive ? 'flex' : 'hidden',
              )}
              aria-hidden={!isActive}
              data-tab={tab.id}
              data-active={isActive ? 'true' : 'false'}
            >
              <Routes location={loc}>
                {tab.id === 'inicio' ? (
                  <Route path="/principal" element={<TelaPrincipalScreen />} />
                ) : null}
                {tab.id === 'mapas' ? (
                  <>
                    <Route path="/mapas" element={<MapasListScreen />} />
                    <Route path="/mapas/novo" element={<MapaFormScreen />} />
                    <Route path="/mapas/:id/editar" element={<MapaFormScreen />} />
                    <Route path="/mapas/:id" element={<MapaDetalheScreen />} />
                  </>
                ) : null}
                {tab.id === 'guia' ? (
                  <>
                    <Route path="/guia" element={<GuiaScreen />} />
                    <Route path="/guia/nova" element={<NovaGuiaScreen />} />
                  </>
                ) : null}
                {tab.id === 'registros' ? (
                  <>
                    <Route path="/registros" element={<RegistrosScreen />} />
                    <Route path="/entrada-saida" element={<EntradaSaidaScreen />} />
                    <Route path="/banco-horas" element={<BancoHorasScreen />} />
                    <Route path="/indicadores" element={<IndicadoresScreen />} />
                  </>
                ) : null}
                {tab.id === 'mais' ? (
                  <>
                    <Route path="/mais" element={<MaisScreen />} />
                    <Route path="/configuracao" element={<ConfiguracaoScreen />} />
                    <Route
                      path="/configuracao/indicadores"
                      element={<IndicadoresConfigScreen />}
                    />
                    <Route path="/usuarios" element={<UsuariosScreen />} />
                  </>
                ) : null}
              </Routes>
            </div>
          );
        })}
      </div>
      <BottomTabBar activeTab={activeTab} onSelect={onSelectTab} />
    </div>
  );
}

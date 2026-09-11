// ----------------------------
// Deus seja Louvado!
// ----------------------------

import type { LucideIcon } from 'lucide-react';
import {
  ClipboardList,
  Home,
  Map,
  MoreHorizontal,
  NotebookTabs,
} from 'lucide-react';

export type MainTabId = 'inicio' | 'mapas' | 'guia' | 'registros' | 'mais';

export type MainTabDef = {
  id: MainTabId;
  label: string;
  /** Rota raiz ao abrir a aba pela primeira vez. */
  path: string;
  icon: LucideIcon;
  match: (pathname: string) => boolean;
};

/** Altura da barra (sem safe-area) — manter alinhado ao BottomTabBar. */
export const MAIN_TAB_BAR_HEIGHT_REM = 3.75;

export const MAIN_TABS: readonly MainTabDef[] = [
  {
    id: 'inicio',
    label: 'Início',
    path: '/principal',
    icon: Home,
    match: (p) => p === '/principal',
  },
  {
    id: 'mapas',
    label: 'Mapas',
    path: '/mapas',
    icon: Map,
    match: (p) => p.startsWith('/mapas'),
  },
  {
    id: 'guia',
    label: 'Guia',
    path: '/guia',
    icon: NotebookTabs,
    match: (p) => p.startsWith('/guia'),
  },
  {
    id: 'registros',
    label: 'Registros',
    path: '/registros',
    icon: ClipboardList,
    match: (p) =>
      p.startsWith('/registros') ||
      p.startsWith('/entrada-saida') ||
      p.startsWith('/banco-horas') ||
      p === '/indicadores' ||
      p.startsWith('/indicadores/'),
  },
  {
    id: 'mais',
    label: 'Mais',
    path: '/mais',
    icon: MoreHorizontal,
    match: (p) =>
      p.startsWith('/mais') ||
      p.startsWith('/configuracao') ||
      p.startsWith('/usuarios'),
  },
] as const;

export function resolveMainTab(pathname: string): MainTabId {
  const hit = MAIN_TABS.find((t) => t.match(pathname));
  return hit?.id ?? 'inicio';
}

export function defaultPathForTab(tabId: MainTabId): string {
  return MAIN_TABS.find((t) => t.id === tabId)?.path ?? '/principal';
}

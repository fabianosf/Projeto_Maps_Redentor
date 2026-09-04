import type { ReactElement, ReactNode } from 'react';
import { render, type RenderOptions } from '@testing-library/react';
import { MemoryRouter, type MemoryRouterProps } from 'react-router-dom';
import type { AuthSession, Permissao } from '@/types/auth';

export function makeAuthSession(
  overrides: Partial<AuthSession> & { codigo_perfil: number },
): AuthSession {
  const codigo = overrides.codigo_perfil;
  let permissoes: Permissao[];
  if (overrides.permissoes) {
    permissoes = [...overrides.permissoes];
  } else if (codigo === 1) {
    permissoes = [
      'principal',
      'guia',
      'entrada-saida',
      'indicadores',
      'mapas',
      'usuarios',
      'configuracao',
      'reset_senha',
    ];
  } else if (codigo === 2) {
    permissoes = ['principal', 'guia', 'entrada-saida', 'indicadores', 'mapas'];
  } else {
    permissoes = [
      'principal',
      'guia',
      'entrada-saida',
      'indicadores',
      'usuarios',
      'configuracao',
    ];
  }

  return {
    matricula: overrides.matricula ?? String(codigo),
    nome: overrides.nome ?? `Usuario ${codigo}`,
    codigo_perfil: codigo as AuthSession['codigo_perfil'],
    permissoes,
  };
}

type Options = Omit<RenderOptions, 'wrapper'> & {
  routerProps?: MemoryRouterProps;
};

export function renderWithProviders(
  ui: ReactElement,
  { routerProps, ...options }: Options = {},
) {
  function Wrapper({ children }: { children: ReactNode }) {
    return <MemoryRouter {...routerProps}>{children}</MemoryRouter>;
  }

  return render(ui, { wrapper: Wrapper, ...options });
}

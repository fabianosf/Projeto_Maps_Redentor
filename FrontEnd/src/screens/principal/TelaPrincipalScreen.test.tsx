import { describe, expect, it, vi } from 'vitest';
import { screen } from '@testing-library/react';
import { TelaPrincipalScreen } from '@/screens/principal/TelaPrincipalScreen';
import { renderWithProviders } from '@/test/test-utils';

const authState = vi.hoisted(() => ({
  perfil: 2 as number,
  nome: 'Despachante',
}));

vi.mock('@/context/AuthContext', () => ({
  useAuth: () => ({
    user: {
      matricula: String(authState.perfil),
      nome: authState.nome,
      codigo_perfil: authState.perfil,
      permissoes:
        authState.perfil === 2
          ? ['principal', 'guia', 'entrada-saida', 'indicadores', 'mapas']
          : [
              'principal',
              'guia',
              'entrada-saida',
              'indicadores',
              'mapas',
              'usuarios',
              'configuracao',
              'reset_senha',
            ],
    },
    loading: false,
    setSessionFromUsuario: vi.fn(),
    clearSession: vi.fn(),
    logout: vi.fn(),
    refresh: vi.fn(),
    hasPermissao: vi.fn(),
  }),
}));

describe('TelaPrincipalScreen', () => {
  it('mostra resumo do dia e atalho Guia', () => {
    authState.perfil = 2;
    authState.nome = 'Despachante';
    renderWithProviders(<TelaPrincipalScreen />);

    expect(screen.getByRole('heading', { name: 'Início' })).toBeInTheDocument();
    expect(screen.getByText(/Resumo do dia/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Guia/i })).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Configuração' })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Sair' })).not.toBeInTheDocument();
  });

  it('exibe Mapas para Despachante', () => {
    authState.perfil = 2;
    authState.nome = 'Despachante';
    renderWithProviders(<TelaPrincipalScreen />);

    expect(screen.getByRole('button', { name: /Mapas/i })).toBeInTheDocument();
  });
});

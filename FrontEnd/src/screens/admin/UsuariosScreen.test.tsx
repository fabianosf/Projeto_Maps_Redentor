import { beforeEach, describe, expect, it, vi } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { UsuariosScreen } from '@/screens/admin/UsuariosScreen';
import { renderWithProviders } from '@/test/test-utils';

const authState = vi.hoisted(() => ({
  perfil: 1 as number,
}));

vi.mock('@/context/AuthContext', () => ({
  useAuth: () => ({
    user: {
      matricula: String(authState.perfil),
      nome: `Usuario ${authState.perfil}`,
      codigo_perfil: authState.perfil,
      permissoes:
        authState.perfil === 1
          ? [
              'principal',
              'guia',
              'entrada-saida',
              'indicadores',
              'mapas',
              'usuarios',
              'configuracao',
              'reset_senha',
            ]
          : [
              'principal',
              'guia',
              'entrada-saida',
              'indicadores',
              'usuarios',
              'configuracao',
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

vi.mock('@/api/cadastros', () => ({
  getCadastros: vi.fn().mockResolvedValue({
    ok: true,
    cadastros: {
      empresas: [{ id_empresa: 1, codigo_empresa: 1, descricao: 'Futuro', ativo: 1 }],
      linhas: [],
      turnos: [{ id_turno: 1, codigo_turno: 1, descricao: 'T1', ativo: 1 }],
      locais: [{ id_local: 1, codigo_local: 10, descricao: 'A', ativo: 1 }],
      veiculos: [],
      motoristas: [],
    },
  }),
}));

vi.mock('@/api/users', () => ({
  listPerfis: vi.fn().mockResolvedValue({
    ok: true,
    perfis: [
      { id_perfil: 1, codigo_perfil: 1, descricao: 'Administrador' },
      { id_perfil: 2, codigo_perfil: 2, descricao: 'Despachante' },
      { id_perfil: 3, codigo_perfil: 3, descricao: 'Inspetor' },
    ],
  }),
  createUser: vi.fn(),
  deleteUser: vi.fn(),
  getErpFuncionario: vi.fn(),
  getUserByMatricula: vi.fn(),
  resetUserPassword: vi.fn(),
  updateUserProfile: vi.fn(),
}));

describe('UsuariosScreen', () => {
  beforeEach(() => {
    authState.perfil = 1;
  });

  it('em idle: Salvar e Deletar desabilitados; Novo e Pesquisar habilitados', async () => {
    renderWithProviders(<UsuariosScreen />);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'Novo' })).toBeEnabled();
    });
    expect(screen.getByRole('button', { name: 'Pesquisar' })).toBeEnabled();
    expect(screen.getByRole('button', { name: 'Salvar' })).toBeDisabled();
    expect(screen.getByRole('button', { name: 'Deletar' })).toBeDisabled();
    expect(screen.getByRole('button', { name: 'Reset' })).toBeDisabled();
  });

  it('após Novo: Salvar habilitado; Deletar e Reset ainda desabilitados', async () => {
    const user = userEvent.setup();
    renderWithProviders(<UsuariosScreen />);
    await waitFor(() => expect(screen.getByRole('button', { name: 'Novo' })).toBeEnabled());

    await user.click(screen.getByRole('button', { name: 'Novo' }));
    expect(screen.getByRole('button', { name: 'Salvar' })).toBeEnabled();
    expect(screen.getByRole('button', { name: 'Deletar' })).toBeDisabled();
    expect(screen.getByRole('button', { name: 'Reset' })).toBeDisabled();
  });

  it('Inspetor não habilita Reset mesmo em edição', async () => {
    authState.perfil = 3;
    const { getUserByMatricula } = await import('@/api/users');
    vi.mocked(getUserByMatricula).mockResolvedValue({
      ok: true,
      usuario: {
        id_usuario: 10,
        matricula: '55',
        nome: 'Alvo',
        ativo: 1,
        trocar_senha: 0,
        codigo_perfil: 2,
        id_perfil: 2,
        perfil_descricao: 'Despachante',
        id_empresa: 1,
        id_turno: 1,
        id_local: 1,
      },
    });

    const user = userEvent.setup();
    renderWithProviders(<UsuariosScreen />);
    await waitFor(() => expect(screen.getByRole('button', { name: 'Pesquisar' })).toBeEnabled());

    await user.click(screen.getByRole('button', { name: 'Pesquisar' }));
    const dialogInput = await screen.findByLabelText(/^matrícula$/i);
    await user.clear(dialogInput);
    await user.type(dialogInput, '55');
    await user.click(screen.getByRole('button', { name: 'OK' }));

    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'Deletar' })).toBeEnabled();
    });
    expect(screen.getByRole('button', { name: 'Reset' })).toBeDisabled();
  });
});

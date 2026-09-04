import { beforeEach, describe, expect, it, vi } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { GuiaScreen } from '@/screens/principal/GuiaScreen';
import { renderWithProviders } from '@/test/test-utils';

vi.mock('@/context/AuthContext', () => ({
  useAuth: () => ({
    user: {
      matricula: '2',
      nome: 'Despachante',
      codigo_perfil: 2,
      permissoes: ['principal', 'guia', 'entrada-saida', 'indicadores', 'mapas'],
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
      linhas: [
        {
          id_linha: 1,
          codigo_linha: 101,
          id_empresa: 1,
          descricao: 'Linha 101',
          ativo: 1,
        },
      ],
      turnos: [{ id_turno: 1, codigo_turno: 1, descricao: 'TURNO 01', ativo: 1 }],
      locais: [],
      veiculos: [{ id_veiculo: 1, numero_frota: '100', placa: 'ABC1D23', ativo: 1 }],
      motoristas: [{ id_motorista: 1, matricula: '50001', nome: 'Mot', ativo: 1 }],
    },
  }),
}));

vi.mock('@/api/guia', () => ({
  createGuia: vi.fn(),
  deleteGuia: vi.fn(),
  getGuiaByNumero: vi.fn(),
  updateGuia: vi.fn(),
}));

describe('GuiaScreen', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('idle: Salvar e Deletar desabilitados', async () => {
    renderWithProviders(<GuiaScreen />);
    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'Novo' })).toBeEnabled();
    });
    expect(screen.getByRole('button', { name: 'Pesquisar' })).toBeEnabled();
    expect(screen.getByRole('button', { name: 'Salvar' })).toBeDisabled();
    expect(screen.getByRole('button', { name: 'Deletar' })).toBeDisabled();
  });

  it('após Novo: Salvar habilitado', async () => {
    const user = userEvent.setup();
    renderWithProviders(<GuiaScreen />);
    await waitFor(() => expect(screen.getByRole('button', { name: 'Novo' })).toBeEnabled());
    await user.click(screen.getByRole('button', { name: 'Novo' }));
    expect(screen.getByRole('button', { name: 'Salvar' })).toBeEnabled();
    expect(screen.getByRole('button', { name: 'Deletar' })).toBeDisabled();
  });

  it('valida HH:MM inválido no início', async () => {
    const user = userEvent.setup();
    renderWithProviders(<GuiaScreen />);
    await waitFor(() => expect(screen.getByRole('button', { name: 'Novo' })).toBeEnabled());
    await user.click(screen.getByRole('button', { name: 'Novo' }));

    await user.type(screen.getByLabelText(/nr\(guia\)/i), 'G1');
    const inicio = screen.getByLabelText(/início\(jornada\)/i);
    await user.clear(inicio);
    await user.type(inicio, '99:99');
    await user.click(screen.getByRole('button', { name: 'Salvar' }));

    expect(
      await screen.findByText('INÍCIO(JORNADA) inválido.'),
    ).toBeInTheDocument();
  });
});

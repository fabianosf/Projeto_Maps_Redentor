import { beforeEach, describe, expect, it, vi } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { EntradaSaidaScreen } from '@/screens/principal/EntradaSaidaScreen';
import { renderWithProviders } from '@/test/test-utils';

const getContexto = vi.fn();
const getLinhasSaida = vi.fn();
const registrar = vi.fn();

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

vi.mock('@/api/entradaSaida', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@/api/entradaSaida')>();
  return {
    ...actual,
    getEntradaSaidaContexto: (...args: unknown[]) => getContexto(...args),
    getLinhasSaidaReferencia: (...args: unknown[]) => getLinhasSaida(...args),
    registrarEntradaSaida: (...args: unknown[]) => registrar(...args),
  };
});

const linha = {
  id_linha: 1,
  codigo_linha: 101,
  descricao: 'Linha 101',
  id_local_origem: 1,
  id_local_destino: 2,
  codigo_origem: 10,
  descricao_origem: 'A',
  codigo_destino: 20,
  descricao_destino: 'B',
};

describe('EntradaSaidaScreen', () => {
  beforeEach(() => {
    getContexto.mockReset();
    getLinhasSaida.mockReset();
    registrar.mockReset();
  });

  it('mostra EmptyState quando não há linhas', async () => {
    getContexto.mockResolvedValue({
      ok: true,
      id_local_usuario: null,
      local_usuario: null,
      linhas: [],
      locais: [],
    });

    renderWithProviders(<EntradaSaidaScreen />);
    expect(await screen.findByText('Usuário sem local')).toBeInTheDocument();
  });

  it('limpa campos de Chegada ao trocar para Saída', async () => {
    getContexto.mockResolvedValue({
      ok: true,
      id_local_usuario: 1,
      local_usuario: { id_local: 1, codigo_local: 10, descricao: 'A' },
      linhas: [linha],
      locais: [{ id_local: 1, codigo_local: 10, descricao: 'A' }],
    });
    getLinhasSaida.mockResolvedValue({ ok: true, linhas: [linha] });

    const user = userEvent.setup();
    renderWithProviders(<EntradaSaidaScreen />);

    const option = await screen.findByRole('option', { name: /101-Linha 101/i });
    await user.click(option);

    const carroChegada = await screen.findByLabelText(/^carro$/i, {
      selector: '#ent_carro',
    });
    await user.type(carroChegada, '100');
    const horarioChegada = screen.getByLabelText(/^chegada$/i, {
      selector: '#ent_horario',
    });
    await user.type(horarioChegada, '0830');
    expect(carroChegada).toHaveValue('100');

    await user.click(screen.getByRole('tab', { name: 'Saída' }));
    await user.click(screen.getByRole('tab', { name: 'Chegada' }));

    await waitFor(() => {
      expect(screen.getByLabelText(/^carro$/i, { selector: '#ent_carro' })).toHaveValue(
        '',
      );
    });
    expect(
      screen.getByLabelText(/^chegada$/i, { selector: '#ent_horario' }),
    ).toHaveValue('');
  });
});

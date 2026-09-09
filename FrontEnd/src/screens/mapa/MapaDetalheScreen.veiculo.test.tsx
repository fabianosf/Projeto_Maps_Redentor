import { beforeEach, describe, expect, it, vi } from 'vitest';
import { Route, Routes } from 'react-router-dom';
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MapaDetalheScreen } from '@/screens/mapa/MapaDetalheScreen';
import { renderWithProviders } from '@/test/test-utils';

const getCadastrosMock = vi.fn();
const createVeiculoMock = vi.fn();
const getMapaMock = vi.fn();
const createItemMock = vi.fn();
const updateItemMock = vi.fn();

vi.mock('@/api/cadastros', () => ({
  getCadastros: (...args: unknown[]) => getCadastrosMock(...args),
  createVeiculo: (...args: unknown[]) => createVeiculoMock(...args),
}));

vi.mock('@/api/mapa', () => ({
  getMapa: (...args: unknown[]) => getMapaMock(...args),
  createItem: (...args: unknown[]) => createItemMock(...args),
  updateItem: (...args: unknown[]) => updateItemMock(...args),
  createViagem: vi.fn(),
  deleteItem: vi.fn(),
  deleteMapa: vi.fn(),
  deleteViagem: vi.fn(),
  listOcupacaoEscalas: vi.fn().mockResolvedValue({
    ok: true,
    veiculos_ocupados: [],
    motoristas_ocupados: [],
    veiculos: [],
    motoristas: [],
  }),
  darBaixaItem: vi.fn(),
}));

vi.mock('@/context/AuthContext', () => ({
  useAuth: () => ({
    user: {
      matricula: '59817',
      nome: 'Teste',
      codigo_perfil: 1,
      permissoes: ['mapas', 'principal'],
    },
    loading: false,
    setSessionFromUsuario: vi.fn(),
    clearSession: vi.fn(),
    logout: vi.fn(),
    refresh: vi.fn(),
    hasPermissao: () => true,
  }),
}));

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>(
    'react-router-dom',
  );
  return {
    ...actual,
    useParams: () => ({ id: '10' }),
  };
});

describe('MapaDetalheScreen — Veículo digitado (modal)', () => {
  beforeEach(() => {
    getCadastrosMock.mockReset();
    createVeiculoMock.mockReset();
    getMapaMock.mockReset();
    createItemMock.mockReset();
    updateItemMock.mockReset();

    getCadastrosMock.mockResolvedValue({
      ok: true,
      cadastros: {
        empresas: [
          { id_empresa: 1, descricao: 'Futuro', ativo: 1 },
          { id_empresa: 2, descricao: 'Redentor', ativo: 1 },
          { id_empresa: 3, descricao: 'Barra', ativo: 1 },
        ],
        linhas: [
          {
            id_linha: 1,
            codigo_linha: 100,
            id_empresa: 1,
            descricao: 'Linha Futuro',
            ativo: 1,
          },
        ],
        turnos: [],
        locais: [],
        veiculos: [],
        motoristas: [
          { id_motorista: 1, matricula: '111', nome: 'Motorista A', ativo: 1 },
        ],
      },
    });
    getMapaMock.mockResolvedValue({
      ok: true,
      mapa: {
        id_registro: 10,
        cod_map: 10,
        id_usuario: 1,
        id_turno: 1,
        data: '2026-09-09',
        inicio_jornada_des: '2026-09-09 05:00:00',
        fim_jornada_des: '2026-09-09 14:00:00',
        turno: 'TURNO 01',
        despachante: 'Teste',
        itens: [],
      },
    });
  });

  it('campo VEÍCULO inicia vazio e bloqueado sem empresa/linha; cancelar não grava', async () => {
    const user = userEvent.setup({ pointerEventsCheck: 0 });
    renderWithProviders(
      <Routes>
        <Route path="/mapas/:id" element={<MapaDetalheScreen />} />
      </Routes>,
      { routerProps: { initialEntries: ['/mapas/10'] } },
    );

    await screen.findByText(/nenhum veículo neste mapa/i);
    await user.click(screen.getByRole('button', { name: /vincular motorista/i }));
    expect(
      await screen.findByRole('heading', { name: /vincular motorista/i }),
    ).toBeInTheDocument();

    const input = screen.getByLabelText(/^veículo/i) as HTMLInputElement;
    expect(input.value).toBe('');
    expect(input).toBeDisabled();
    expect(input.placeholder).toBe('Selecione empresa e linha antes');

    await user.click(screen.getByRole('button', { name: /^cancelar$/i }));
    await waitFor(() => {
      expect(
        screen.queryByRole('heading', { name: /vincular motorista/i }),
      ).not.toBeInTheDocument();
    });
    expect(createItemMock).not.toHaveBeenCalled();
    expect(createVeiculoMock).not.toHaveBeenCalled();
    expect(updateItemMock).not.toHaveBeenCalled();
  });
});

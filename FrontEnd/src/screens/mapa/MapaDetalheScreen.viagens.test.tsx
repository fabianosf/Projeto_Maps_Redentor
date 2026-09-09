import { beforeEach, describe, expect, it, vi } from 'vitest';
import { Route, Routes } from 'react-router-dom';
import { screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MapaDetalheScreen } from '@/screens/mapa/MapaDetalheScreen';
import { renderWithProviders } from '@/test/test-utils';
import type { MapaCompleto } from '@/types/mapa';

const getCadastrosMock = vi.fn();
const getMapaMock = vi.fn();
const createViagemMock = vi.fn();

vi.mock('@/api/cadastros', () => ({
  getCadastros: (...args: unknown[]) => getCadastrosMock(...args),
  createVeiculo: vi.fn(),
}));

vi.mock('@/api/mapa', () => ({
  getMapa: (...args: unknown[]) => getMapaMock(...args),
  createItem: vi.fn(),
  updateItem: vi.fn(),
  createViagem: (...args: unknown[]) => createViagemMock(...args),
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

function mapaDoisItens(): MapaCompleto {
  return {
    id_registro: 10,
    cod_map: 10,
    id_usuario: 1,
    id_turno: 1,
    data: '2026-09-09',
    inicio_jornada_des: '2026-09-09 05:00:00',
    fim_jornada_des: '2026-09-09 14:00:00',
    turno: 'TURNO 01',
    despachante: 'Teste',
    itens: [
      {
        id_item: 101,
        id_mapa_item: 101,
        idmap: 10,
        id_linha: 1,
        id_veiculo: 1,
        id_motorista: 1,
        hor_ini_jor: '2026-09-09 08:00:00',
        hor_fim_jor: '2026-09-09 12:00:00',
        chegada_ponto: '2026-09-09 08:10:00',
        status_escala: 'EM_ANDAMENTO',
        empresa: 'Futuro',
        codigo_linha: 550,
        numero_frota: 'C30000',
        motorista: 'João da Silva',
        matricula_motorista: '2001',
        viagens: [
          {
            id_viagem: 1,
            id_item_registro: 101,
            id_mapa_item: 101,
            horario_saida: '2026-09-09 09:00:00',
            horario_chegada: '2026-09-09 10:00:00',
            qtd_pas_ida: 5,
            qtd_pas_volta: 2,
          },
        ],
      },
      {
        id_item: 102,
        id_mapa_item: 102,
        idmap: 10,
        id_linha: 2,
        id_veiculo: 2,
        id_motorista: 2,
        hor_ini_jor: '2026-09-09 13:00:00',
        hor_fim_jor: '2026-09-09 17:00:00',
        chegada_ponto: '2026-09-09 13:10:00',
        status_escala: 'EM_ANDAMENTO',
        empresa: 'Futuro',
        codigo_linha: 202,
        numero_frota: 'C30002',
        motorista: 'Maria Souza',
        matricula_motorista: '3002',
        viagens: [
          {
            id_viagem: 2,
            id_item_registro: 102,
            id_mapa_item: 102,
            horario_saida: '2026-09-09 14:00:00',
            horario_chegada: '2026-09-09 15:00:00',
            qtd_pas_ida: 3,
            qtd_pas_volta: 1,
          },
        ],
      },
    ],
  };
}

function renderDetalhe() {
  return renderWithProviders(
    <Routes>
      <Route path="/mapas/:id" element={<MapaDetalheScreen />} />
    </Routes>,
    { routerProps: { initialEntries: ['/mapas/10'] } },
  );
}

describe('MapaDetalheScreen — viagens por item/motorista', () => {
  beforeEach(() => {
    getCadastrosMock.mockReset();
    getMapaMock.mockReset();
    createViagemMock.mockReset();

    getCadastrosMock.mockResolvedValue({
      ok: true,
      cadastros: {
        empresas: [],
        linhas: [],
        turnos: [],
        locais: [],
        veiculos: [],
        motoristas: [],
      },
    });
    getMapaMock.mockResolvedValue({ ok: true, mapa: mapaDoisItens() });
    createViagemMock.mockResolvedValue({
      ok: true,
      viagem: {
        id_viagem: 99,
        id_item_registro: 101,
        id_mapa_item: 101,
        horario_saida: '2026-09-09 11:00:00',
        horario_chegada: '2026-09-09 12:00:00',
        qtd_pas_ida: 0,
        qtd_pas_volta: 0,
      },
    });
  });

  it('sem seleção: mensagem, sem viagens e botão Nova viagem desabilitado', async () => {
    renderDetalhe();
    await waitFor(() => {
      expect(screen.getByText(/selecione um veículo e motorista/i)).toBeInTheDocument();
    });
    expect(screen.queryByText(/Viagens —/i)).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: /nova viagem/i })).toBeDisabled();
  });

  it('cada item mostra só as próprias viagens e o resumo do motorista', async () => {
    const user = userEvent.setup();
    renderDetalhe();
    await waitFor(() => {
      expect(screen.getByText('C30000')).toBeInTheDocument();
    });

    await user.click(screen.getByText('C30000'));
    await waitFor(() => {
      expect(screen.getByText(/Viagens — C30000/i)).toBeInTheDocument();
    });
    expect(screen.getByText(/Motorista:/i).parentElement).toHaveTextContent(
      /2001 — João da Silva/,
    );
    expect(screen.getByText(/Linha 550/i)).toHaveTextContent(/Futuro/);
    expect(screen.getByText(/Jornada/i)).toBeInTheDocument();
    expect(screen.getByText('5')).toBeInTheDocument();
    expect(screen.queryByText('3')).not.toBeInTheDocument();

    await user.click(screen.getByText('C30002'));
    await waitFor(() => {
      expect(screen.getByText(/Viagens — C30002/i)).toBeInTheDocument();
    });
    expect(screen.getByText(/Motorista:/i).parentElement).toHaveTextContent(
      /3002 — Maria Souza/,
    );
    expect(screen.getByText('3')).toBeInTheDocument();
    expect(screen.queryByText('5')).not.toBeInTheDocument();
  });

  it('Nova viagem envia id_mapa_item no payload', async () => {
    const user = userEvent.setup();
    renderDetalhe();
    await waitFor(() => {
      expect(screen.getByText('C30000')).toBeInTheDocument();
    });
    await user.click(screen.getByText('C30000'));

    await user.click(screen.getByRole('button', { name: /nova viagem/i }));
    const dialog = await screen.findByRole('dialog');
    const saida = within(dialog).getByLabelText(/^saída/i);
    const chegada = within(dialog).getByLabelText(/^chegada/i);
    await user.clear(saida);
    await user.type(saida, '11:00');
    await user.clear(chegada);
    await user.type(chegada, '12:00');
    await user.click(within(dialog).getByRole('button', { name: /confirmar/i }));

    await waitFor(() => {
      expect(createViagemMock).toHaveBeenCalled();
    });
    const [idItem, payload] = createViagemMock.mock.calls[0];
    expect(idItem).toBe(101);
    expect(payload.id_mapa_item).toBe(101);
    expect(payload.id_item).toBe(101);
  });
});

import { beforeEach, describe, expect, it, vi } from 'vitest';
import { Route, Routes } from 'react-router-dom';
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MapaFormScreen } from '@/screens/mapa/MapaFormScreen';
import { MapasListScreen } from '@/screens/mapa/MapasListScreen';
import { renderWithProviders } from '@/test/test-utils';

const getCadastrosMock = vi.fn();
const listMapasMock = vi.fn();
const createMapaMock = vi.fn();
const getMapaMock = vi.fn();
const updateMapaMock = vi.fn();

vi.mock('@/api/cadastros', () => ({
  getCadastros: (...args: unknown[]) => getCadastrosMock(...args),
}));

vi.mock('@/api/mapa', () => ({
  listMapas: (...args: unknown[]) => listMapasMock(...args),
  createMapa: (...args: unknown[]) => createMapaMock(...args),
  getMapa: (...args: unknown[]) => getMapaMock(...args),
  updateMapa: (...args: unknown[]) => updateMapaMock(...args),
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

function renderNovoMapaFlow() {
  return renderWithProviders(
    <Routes>
      <Route path="/mapas" element={<MapasListScreen />} />
      <Route path="/mapas/novo" element={<MapaFormScreen />} />
    </Routes>,
    { routerProps: { initialEntries: ['/mapas/novo'] } },
  );
}

describe('MapaFormScreen Cancelar', () => {
  beforeEach(() => {
    getCadastrosMock.mockReset();
    listMapasMock.mockReset();
    createMapaMock.mockReset();
    getMapaMock.mockReset();
    updateMapaMock.mockReset();

    getCadastrosMock.mockResolvedValue({
      ok: true,
      cadastros: {
        empresas: [
          {
            id_empresa: 1,
            codigo_empresa: 1,
            descricao: 'Futuro',
            prefixo_mapa: 'Fut',
            ativo: 1,
          },
        ],
        linhas: [],
        turnos: [
          { id_turno: 1, codigo_turno: 1, descricao: 'TURNO 01', ativo: 1 },
        ],
        locais: [],
        veiculos: [],
        motoristas: [],
      },
    });

    listMapasMock.mockResolvedValue({
      ok: true,
      mapas: [
        {
          id_registro: 1,
          cod_map: 1,
          data: '2026-09-09',
          linha: '100',
          turno: 'TURNO 01',
        },
      ],
    });
  });

  it('Cancelar em Novo MAPA volta à lista sem criar e sem erro startTime', async () => {
    const user = userEvent.setup();
    const pageErrors: string[] = [];
    const onError = (ev: ErrorEvent) => {
      pageErrors.push(String(ev.message ?? ev.error ?? ''));
    };
    window.addEventListener('error', onError);

    try {
      renderNovoMapaFlow();

      expect(
        await screen.findByRole('button', { name: /^cancelar$/i }),
      ).toBeInTheDocument();

      await user.click(screen.getByRole('button', { name: /^cancelar$/i }));

      await waitFor(() => {
        expect(
          screen.getByRole('heading', { name: /^mapas$/i }),
        ).toBeInTheDocument();
      });

      expect(createMapaMock).not.toHaveBeenCalled();
      expect(updateMapaMock).not.toHaveBeenCalled();
      expect(
        pageErrors.some((m) => /startTime|reportAllChanges/i.test(m)),
      ).toBe(false);
    } finally {
      window.removeEventListener('error', onError);
    }
  });

  it('criação sem empresa não dispara POST', async () => {
    const user = userEvent.setup();
    renderNovoMapaFlow();

    const inicio = await screen.findByLabelText(/in[ií]cio do plant[aã]o/i);
    expect(inicio).toHaveAttribute('type', 'time');
    await user.click(screen.getByRole('button', { name: /^confirmar$/i }));

    await waitFor(() => {
      expect(createMapaMock).not.toHaveBeenCalled();
    });
    expect(
      screen.getByRole('button', { name: /^confirmar$/i }),
    ).toBeInTheDocument();
  });
});

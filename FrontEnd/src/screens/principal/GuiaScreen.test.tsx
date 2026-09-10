import { beforeEach, describe, expect, it, vi } from 'vitest';
import { screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { GuiaScreen } from '@/screens/principal/GuiaScreen';
import { renderWithProviders } from '@/test/test-utils';
import * as guiaApi from '@/api/guia';
import { ApiRequestError } from '@/api/client';

vi.mock('@/context/AuthContext', () => ({
  useAuth: () => ({
    user: {
      matricula: '2',
      nome: 'Despachante Silva',
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
          codigo_linha: 24,
          id_empresa: 1,
          descricao: 'Linha 24',
          ativo: 1,
        },
      ],
      turnos: [{ id_turno: 1, codigo_turno: 1, descricao: 'manhã', ativo: 1 }],
      locais: [],
      veiculos: [{ id_veiculo: 1, numero_frota: '100', placa: 'ABC1D23', ativo: 1 }],
      motoristas: [{ id_motorista: 1, matricula: '50001', nome: 'Mot', ativo: 1 }],
    },
  }),
}));

vi.mock('@/api/guia', () => ({
  listGuias: vi.fn(),
  createGuia: vi.fn(),
  deleteGuia: vi.fn(),
  getGuiaByNumero: vi.fn(),
  updateGuia: vi.fn(),
  registrarAjusteManual: vi.fn(),
  salvarRoletaLeitura: vi.fn(),
  sugerirRoletaInicial: vi.fn(),
  listEscalasGuia: vi.fn(),
  getContextoEscala: vi.fn(),
  registrarAlteracaoEscala: vi.fn(),
  getHistoricoRoleta: vi.fn(),
}));

const navigateMock = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>(
    'react-router-dom',
  );
  return {
    ...actual,
    useNavigate: () => navigateMock,
  };
});

const guiaSample = {
  id_guia: 10,
  numero: '024',
  id_empresa: 1,
  id_linha: 1,
  id_turno: 1,
  numero_frota: '102345',
  matricula_motorista: '50001',
  hor_ini: '2026-09-10 07:10:00',
  hor_fim: '2026-09-10 08:42:00',
  roleta01_ini: 100,
  roleta01_fim: 136,
  roleta2_ini: 200,
  roleta2_fim: 250,
  observacao: null,
  linha_codigo: '024',
  turno_descricao: 'manhã',
};

const consolidadoOk = {
  ok: true as const,
  data: '10/09/2026',
  status: 'sincronizado' as const,
  resumo: {
    titulo_mapa: 'Mapa 024',
    turno: 'Turno manhã',
    cod_map: 24,
    ida: { jae: 36, riocard: 10 },
    volta: { jae: 50, riocard: 8 },
    total_viagens: 2,
    ultima_leitura: '08:42',
  },
  viagens: [
    {
      key: 'v-1-ida',
      viagem_label: 'Viagem 01',
      id_viagem: 1,
      id_guia: 10,
      mapa: 'Mapa 024',
      veiculo: '102345',
      data: '10/09/2026',
      turno: 'manhã',
      sentido: 'ida' as const,
      horario: '07:10',
      embarques: 0,
      origem: 'roleta' as const,
      status: 'sincronizado' as const,
      jae: {
        leitura_ini: 100,
        leitura_fim: 136,
        passageiros: 36,
        status_leitura: 'finalizada' as const,
      },
      riocard: {
        leitura_ini: 10,
        leitura_fim: 20,
        passageiros: 10,
        status_leitura: 'finalizada' as const,
      },
    },
    {
      key: 'v-1-volta',
      viagem_label: 'Viagem 02',
      id_viagem: 1,
      id_guia: 10,
      mapa: 'Mapa 024',
      veiculo: '102345',
      data: '10/09/2026',
      turno: 'manhã',
      sentido: 'volta' as const,
      horario: '07:10',
      embarques: 0,
      origem: 'roleta' as const,
      status: 'sincronizado' as const,
      jae: {
        leitura_ini: 200,
        leitura_fim: 250,
        passageiros: 50,
        status_leitura: 'finalizada' as const,
      },
      riocard: {
        leitura_ini: 0,
        leitura_fim: 8,
        passageiros: 8,
        status_leitura: 'finalizada' as const,
      },
    },
  ],
  guias: [guiaSample],
};

describe('GuiaScreen', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    navigateMock.mockReset();
    vi.mocked(guiaApi.listGuias).mockResolvedValue(consolidadoOk);
    vi.mocked(guiaApi.getHistoricoRoleta).mockResolvedValue({
      ok: true,
      historico: [],
    });
    vi.mocked(guiaApi.listEscalasGuia).mockResolvedValue({
      ok: true,
      data: '10/09/2026',
      mapas: [
        {
          id_registro: 5,
          cod_map: 24,
          turno: 'manhã',
          label: 'Mapa 24 · manhã',
        },
      ],
      escalas: [
        {
          id_item: 7,
          id_mapa: 5,
          cod_map: 24,
          turno: 'manhã',
          numero_frota: '100',
          matricula_motorista: '50001',
          label: 'Carro 100 · Mot. 50001',
        },
      ],
    });
    vi.mocked(guiaApi.getContextoEscala).mockResolvedValue({
      ok: true,
      contexto: {
        id_item: 7,
        id_mapa: 5,
        cod_map: 24,
        data: '10/09/2026',
        empresa: 'Futuro',
        linha: 'Linha 24',
        codigo_linha: 24,
        turno: 'manhã',
        numero_frota: '100',
        matricula_motorista: '50001',
        motorista: 'Mot',
        chegada_ponto_hhmm: '05:45',
        hor_ini_jor_hhmm: '06:00',
        hor_fim_jor_hhmm: '14:00',
        viagens_previstas: [
          {
            id_viagem: 1,
            horario_saida: '06:30',
            horario_chegada: '07:00',
            qtd_pas_ida: 20,
            qtd_pas_volta: 15,
          },
        ],
      },
    });
  });

  it('exibe resumo e viagens vindos da API (sem consolidar no front)', async () => {
    renderWithProviders(<GuiaScreen />);

    await waitFor(() => {
      expect(screen.getByRole('heading', { name: /mapa 024/i })).toBeInTheDocument();
    });

    expect(screen.getAllByText('Sincronizado').length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText('36').length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText('50').length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText(/última leitura/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/viagem 01, ida/i)).toBeInTheDocument();
    expect(screen.getAllByText('Ja E').length).toBeGreaterThanOrEqual(2);
    expect(screen.getAllByText('RioCard').length).toBeGreaterThanOrEqual(2);
    expect(guiaApi.listGuias).toHaveBeenCalled();
  });

  it('estado vazio quando API retorna sem viagens', async () => {
    vi.mocked(guiaApi.listGuias).mockResolvedValue({
      ...consolidadoOk,
      resumo: {
        ...consolidadoOk.resumo,
        total_viagens: 0,
        ida: { jae: 0, riocard: 0 },
        volta: { jae: 0, riocard: 0 },
      },
      viagens: [],
      guias: [],
    });
    renderWithProviders(<GuiaScreen />);

    expect(await screen.findByText('Nenhuma viagem')).toBeInTheDocument();
    expect(screen.getAllByRole('button', { name: /nova guia/i }).length).toBeGreaterThanOrEqual(1);
  });

  it('estado de erro com retry', async () => {
    vi.mocked(guiaApi.listGuias).mockRejectedValue(new Error('rede'));
    renderWithProviders(<GuiaScreen />);

    expect(await screen.findByText('Falha ao sincronizar')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /tentar de novo/i })).toBeInTheDocument();
  });

  it('exibe mensagem amigável em HTTP 405', async () => {
    vi.mocked(guiaApi.listGuias).mockRejectedValue(
      new ApiRequestError(405, {
        ok: false,
        mensagem:
          'Consulta não disponível neste endereço (método não permitido). Reinicie a API ou tente novamente.',
        codigo: 'metodo_nao_permitido',
      }),
    );
    renderWithProviders(<GuiaScreen />);

    expect(await screen.findByText(/método não permitido/i)).toBeInTheDocument();
  });

  it('abre detalhe da viagem com leituras independentes', async () => {
    const user = userEvent.setup();
    renderWithProviders(<GuiaScreen />);

    await user.click(await screen.findByLabelText(/viagem 01, ida/i));
    const dialog = await screen.findByRole('dialog');
    expect(within(dialog).getByText(/viagem 01/i)).toBeInTheDocument();
    expect(within(dialog).getByText(/leituras \(independentes\)/i)).toBeInTheDocument();
    expect(within(dialog).getAllByText('Ja E').length).toBeGreaterThanOrEqual(1);
    expect(within(dialog).getAllByText('RioCard').length).toBeGreaterThanOrEqual(1);
    expect(within(dialog).getByText(/^Histórico$/i)).toBeInTheDocument();
  });

  it('ajuste manual exige justificativa e chama API dedicada', async () => {
    const user = userEvent.setup();
    vi.mocked(guiaApi.registrarAjusteManual).mockResolvedValue({
      ok: true,
      guia: { ...guiaSample, observacao: '[AM ida=40 09:00]falha' },
      mensagem: 'Ajuste manual registrado com auditoria.',
    });

    renderWithProviders(<GuiaScreen />);
    await user.click(await screen.findByLabelText(/viagem 01, ida/i));
    const dialog = await screen.findByRole('dialog');
    await user.click(within(dialog).getByRole('button', { name: 'Ajuste manual' }));

    const confirmar = await screen.findByRole('button', { name: 'Confirmar' });
    expect(confirmar).toBeDisabled();

    await user.type(screen.getByLabelText(/justificativa/i), 'falha catraca');
    await user.click(confirmar);

    await waitFor(() => {
      expect(guiaApi.registrarAjusteManual).toHaveBeenCalledWith(
        10,
        expect.objectContaining({
          sentido: 'ida',
          justificativa: 'falha catraca',
        }),
      );
    });
  });

  it('abre editor Ja E da viagem', async () => {
    const user = userEvent.setup();
    vi.mocked(guiaApi.salvarRoletaLeitura).mockResolvedValue({
      ok: true,
      leitura: {
        id_leitura: 1,
        sentido: 'ida',
        fonte: 'jae',
        leitura_ini: 100,
        leitura_fim: 140,
        passageiros: 40,
        status_leitura: 'finalizada',
      },
      mensagem: 'Leitura registrada com sucesso.',
    });
    renderWithProviders(<GuiaScreen />);
    const editors = await screen.findAllByLabelText(/editar ja e/i);
    await user.click(editors[0]);
    expect(await screen.findByText(/ja e — ida/i)).toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: 'Salvar' }));
    await waitFor(() => {
      expect(guiaApi.salvarRoletaLeitura).toHaveBeenCalled();
    });
  });

  it('Nova Guia navega para tela distinta', async () => {
    const user = userEvent.setup();
    renderWithProviders(<GuiaScreen />);
    await waitFor(() => {
      expect(screen.getByRole('heading', { name: /mapa 024/i })).toBeInTheDocument();
    });
    await user.click(screen.getAllByRole('button', { name: /nova guia/i })[0]);
    expect(navigateMock).toHaveBeenCalledWith('/guia/nova');
  });
});

import { beforeEach, describe, expect, it, vi } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ApiRequestError } from '@/api/client';
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

  it('após Novo: Salvar permanece desabilitado sem nome; Deletar e Reset desabilitados', async () => {
    const user = userEvent.setup();
    renderWithProviders(<UsuariosScreen />);
    await waitFor(() => expect(screen.getByRole('button', { name: 'Novo' })).toBeEnabled());

    await user.click(screen.getByRole('button', { name: 'Novo' }));
    expect(screen.getByRole('button', { name: 'Salvar' })).toBeDisabled();
    expect(screen.getByRole('button', { name: 'Deletar' })).toBeDisabled();
    expect(screen.getByRole('button', { name: 'Reset' })).toBeDisabled();
  });

  it('Despachante: após ERP, Salvar envia id_empresa, id_turno e id_local', async () => {
    const { getErpFuncionario, createUser } = await import('@/api/users');
    vi.mocked(getErpFuncionario).mockResolvedValue({
      matricula: '59492',
      nome: 'Funcionario Oracle',
      foto_url: null,
      ativo: true,
      origem: 'oracle',
    });
    vi.mocked(createUser).mockResolvedValue({
      ok: true,
      usuario: {
        id_usuario: 99,
        matricula: '59492',
        nome: 'Funcionario Oracle',
        ativo: 1,
        trocar_senha: 1,
        codigo_perfil: 2,
        id_perfil: 2,
        perfil_descricao: 'Despachante',
        id_empresa: 1,
        id_turno: 1,
        id_local: 1,
        senha_temporaria: 'Tmp#1234',
      },
    });

    const user = userEvent.setup();
    renderWithProviders(<UsuariosScreen />);
    await waitFor(() => expect(screen.getByRole('button', { name: 'Novo' })).toBeEnabled());

    await user.click(screen.getByRole('button', { name: 'Novo' }));
    const input = screen.getByLabelText(/matrícula/i);
    await user.type(input, '59492');
    await user.tab();

    await waitFor(() => {
      expect(screen.getByDisplayValue('Funcionario Oracle')).toBeInTheDocument();
    });

    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'Salvar' })).toBeEnabled();
    });
    await user.click(screen.getByRole('button', { name: 'Salvar' }));

    await waitFor(() => {
      expect(createUser).toHaveBeenCalled();
    });
    expect(createUser).toHaveBeenCalledWith(
      '59492',
      'Funcionario Oracle',
      2,
      { id_empresa: 1, id_turno: 1, id_local: 1 },
    );
  });

  it('Inspetor não habilita Reset mesmo em edição', async () => {
    authState.perfil = 3;
    const { getUserByMatricula } = await import('@/api/users');
    vi.mocked(getUserByMatricula).mockResolvedValue({
      ok: true,
      ja_cadastrado: true,
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

    // Fecha o alerta de "Usuário já cadastrado."
    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'OK' })).toBeInTheDocument();
    });
    await user.click(screen.getByRole('button', { name: 'OK' }));

    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'Deletar' })).toBeEnabled();
    });
    expect(screen.getByRole('button', { name: 'Reset' })).toBeDisabled();
  });

  it('Pesquisar preenche inclusão quando matrícula existe só no RH', async () => {
    const { getUserByMatricula } = await import('@/api/users');
    vi.mocked(getUserByMatricula).mockResolvedValue({
      ok: true,
      ja_cadastrado: false,
      mensagem: 'Matrícula localizada no RH. Complete o cadastro e salve.',
      usuario: {
        matricula: '59548',
        nome: 'Funcionario RH',
        foto_url: null,
        origem: 'oracle',
        ativo: true,
      },
    });

    const user = userEvent.setup();
    renderWithProviders(<UsuariosScreen />);
    await waitFor(() => expect(screen.getByRole('button', { name: 'Pesquisar' })).toBeEnabled());

    await user.click(screen.getByRole('button', { name: 'Pesquisar' }));
    const dialogInput = await screen.findByLabelText(/^matrícula$/i);
    await user.clear(dialogInput);
    await user.type(dialogInput, '59548');
    await user.click(screen.getByRole('button', { name: 'OK' }));

    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'OK' })).toBeInTheDocument();
    });
    await user.click(screen.getByRole('button', { name: 'OK' }));

    await waitFor(() => {
      expect(screen.getByDisplayValue('59548')).toBeInTheDocument();
      expect(screen.getByDisplayValue('Funcionario RH')).toBeInTheDocument();
    });
    expect(screen.getByDisplayValue('Funcionario RH')).toHaveAttribute('readonly');
    expect(screen.getByRole('status')).toHaveTextContent('59548');
  });

  it('preenche nome após consulta do cadastro corporativo', async () => {
    const { getErpFuncionario } = await import('@/api/users');
    vi.mocked(getErpFuncionario).mockResolvedValue({
      matricula: '59492',
      nome: 'Funcionario Oracle',
      foto_url: null,
      ativo: true,
      origem: 'oracle',
    });

    const user = userEvent.setup();
    renderWithProviders(<UsuariosScreen />);
    await waitFor(() => expect(screen.getByRole('button', { name: 'Novo' })).toBeEnabled());

    await user.click(screen.getByRole('button', { name: 'Novo' }));
    const input = screen.getByLabelText(/matrícula/i);
    await user.type(input, ' 59 492 ');
    await user.tab();

    await waitFor(() => {
      expect(screen.getByDisplayValue('Funcionario Oracle')).toBeInTheDocument();
    });
    expect(screen.getByRole('status')).toHaveTextContent('59492');
    expect(screen.getByDisplayValue('Funcionario Oracle')).toHaveAttribute('readonly');
  });

  it('mostra mensagem correta quando matrícula não existe', async () => {
    const { getErpFuncionario } = await import('@/api/users');
    vi.mocked(getErpFuncionario).mockRejectedValue(
      new ApiRequestError(404, {
        codigo: 'funcionario_nao_encontrado',
        mensagem: 'Matrícula não encontrada no cadastro de funcionários.',
        ok: false,
      }),
    );

    const user = userEvent.setup();
    renderWithProviders(<UsuariosScreen />);
    await waitFor(() => expect(screen.getByRole('button', { name: 'Novo' })).toBeEnabled());

    await user.click(screen.getByRole('button', { name: 'Novo' }));
    const input = screen.getByLabelText(/matrícula/i);
    await user.type(input, '59492');
    await user.tab();

    await waitFor(() => {
      expect(screen.getByRole('alert')).toHaveTextContent(
        'Matrícula não encontrada no cadastro de funcionários. Confira o número informado.',
      );
    });
  });

  it('mostra mensagem correta em 503 e sai do loading', async () => {
    const { getErpFuncionario } = await import('@/api/users');
    vi.mocked(getErpFuncionario).mockImplementation(
      () =>
        new Promise((_, reject) =>
          setTimeout(
            () =>
              reject(
                new ApiRequestError(503, {
                  codigo: 'erp_indisponivel',
                  mensagem:
                    'Não foi possível consultar o cadastro corporativo no momento. Tente novamente.',
                  ok: false,
                }),
              ),
            0,
          ),
        ) as never,
    );

    const user = userEvent.setup();
    renderWithProviders(<UsuariosScreen />);
    await waitFor(() => expect(screen.getByRole('button', { name: 'Novo' })).toBeEnabled());

    await user.click(screen.getByRole('button', { name: 'Novo' }));
    const input = screen.getByLabelText(/matrícula/i);
    await user.type(input, '59800');
    await user.tab();

    expect(await screen.findByRole('alert')).toHaveTextContent(
      'Cadastro corporativo indisponível. Tente novamente.',
    );
    await waitFor(() => {
      expect(screen.queryByText('Consultando cadastro...')).not.toBeInTheDocument();
    });
    expect(screen.getByRole('button', { name: 'Pesquisar' })).toBeEnabled();
  });
});

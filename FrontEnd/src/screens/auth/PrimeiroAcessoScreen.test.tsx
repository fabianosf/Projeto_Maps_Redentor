import { beforeEach, describe, expect, it, vi } from 'vitest';
import { screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { PrimeiroAcessoScreen } from '@/screens/auth/PrimeiroAcessoScreen';
import { renderWithProviders } from '@/test/test-utils';

const changePasswordMock = vi.fn();
const cancelChangePasswordMock = vi.fn();
const loginMock = vi.fn();
const setSessionFromUsuario = vi.fn();
const clearSession = vi.fn();

vi.mock('@/api/auth', () => ({
  changePassword: (...args: unknown[]) => changePasswordMock(...args),
  cancelChangePassword: (...args: unknown[]) => cancelChangePasswordMock(...args),
  login: (...args: unknown[]) => loginMock(...args),
}));

vi.mock('@/context/AuthContext', () => ({
  useAuth: () => ({
    user: null,
    loading: false,
    setSessionFromUsuario,
    clearSession,
    logout: vi.fn(),
    refresh: vi.fn(),
    hasPermissao: vi.fn(),
  }),
}));

function renderPrimeiroAcesso() {
  return renderWithProviders(<PrimeiroAcessoScreen />, {
    routerProps: {
      initialEntries: [
        {
          pathname: '/primeiro-acesso',
          state: { changeToken: 'tok-abc', matricula: '99' },
        },
      ],
    },
  });
}

describe('PrimeiroAcessoScreen', () => {
  beforeEach(() => {
    changePasswordMock.mockReset();
    cancelChangePasswordMock.mockReset();
    loginMock.mockReset();
  });

  it('exige senhas iguais', async () => {
    const user = userEvent.setup();
    renderPrimeiroAcesso();

    await user.type(screen.getByLabelText(/nova senha/i), 'Senha@123');
    await user.type(screen.getByLabelText(/confirmar senha/i), 'Outra@123');
    await user.click(screen.getByRole('button', { name: /salvar senha/i }));

    expect(
      (await screen.findAllByText('Senhas digitadas diferentes!')).length,
    ).toBeGreaterThan(0);
    expect(changePasswordMock).not.toHaveBeenCalled();
  }, 15000);

  it('rejeita senha fora da política', async () => {
    const user = userEvent.setup();
    renderPrimeiroAcesso();

    await user.type(screen.getByLabelText(/nova senha/i), 'fraca');
    await user.type(screen.getByLabelText(/confirmar senha/i), 'fraca');
    await user.click(screen.getByRole('button', { name: /salvar senha/i }));

    expect(
      (await screen.findAllByText('Senha inválida!')).length,
    ).toBeGreaterThan(0);
    expect(changePasswordMock).not.toHaveBeenCalled();
  }, 15000);

  it('aceita senha válida e chama API', async () => {
    const user = userEvent.setup();
    changePasswordMock.mockResolvedValue({
      ok: true,
      mensagem: 'senha cadastrada com sucesso!',
    });
    loginMock.mockResolvedValue({
      ok: true,
      trocar_senha: false,
      usuario: {
        id_usuario: 4,
        matricula: '99',
        nome: 'Novo',
        codigo_perfil: 2,
        trocar_senha: false,
      },
    });

    renderPrimeiroAcesso();
    const senha = 'Senha@123';
    await user.type(screen.getByLabelText(/nova senha/i), senha);
    await user.type(screen.getByLabelText(/confirmar senha/i), senha);
    await user.click(screen.getByRole('button', { name: /salvar senha/i }));

    expect(changePasswordMock).toHaveBeenCalledWith('tok-abc', senha, senha);
  }, 15000);
});

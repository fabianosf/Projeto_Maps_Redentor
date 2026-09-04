import { beforeEach, describe, expect, it, vi } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { LoginScreen } from '@/screens/auth/LoginScreen';
import { renderWithProviders } from '@/test/test-utils';

const loginMock = vi.fn();
const cancelLoginMock = vi.fn();
const setSessionFromUsuario = vi.fn();
const clearSession = vi.fn();

vi.mock('@/api/auth', () => ({
  login: (...args: unknown[]) => loginMock(...args),
  cancelLogin: (...args: unknown[]) => cancelLoginMock(...args),
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

describe('LoginScreen', () => {
  beforeEach(() => {
    loginMock.mockReset();
    cancelLoginMock.mockReset();
    setSessionFromUsuario.mockReset();
    clearSession.mockReset();
  });

  it('foca matrícula ao montar', async () => {
    renderWithProviders(<LoginScreen />);
    const mat = await screen.findByLabelText(/matrícula/i);
    await waitFor(() => expect(mat).toHaveFocus(), { timeout: 200 });
  });

  it('valida matrícula vazia antes da API', async () => {
    const user = userEvent.setup();
    renderWithProviders(<LoginScreen />);

    await user.click(screen.getByRole('button', { name: /confirmar/i }));
    expect(await screen.findByText('Matrícula inválida!')).toBeInTheDocument();
    expect(loginMock).not.toHaveBeenCalled();
  });

  it('valida senha após matrícula válida', async () => {
    const user = userEvent.setup();
    renderWithProviders(<LoginScreen />);

    await user.type(screen.getByLabelText(/matrícula/i), '123');
    await user.click(screen.getByRole('button', { name: /confirmar/i }));
    expect(await screen.findByText('Senha inválida!')).toBeInTheDocument();
    expect(loginMock).not.toHaveBeenCalled();
  });

  it('Enter na matrícula move o foco para senha', async () => {
    const user = userEvent.setup();
    renderWithProviders(<LoginScreen />);

    const mat = screen.getByLabelText(/matrícula/i);
    const senha = screen.getByLabelText(/^senha$/i);
    await user.type(mat, '123');
    await user.keyboard('{Enter}');
    expect(senha).toHaveFocus();
  });
});

import { apiFetch } from './client';
import type {
  ChangePasswordResponse,
  LoginResponse,
  MeResponse,
} from '@/types/auth';

export async function login(matricula: string, senha: string): Promise<LoginResponse> {
  return apiFetch<LoginResponse>('/auth/login', {
    method: 'POST',
    body: { matricula, senha },
    skipSessionExpired: true,
  });
}

export async function changePassword(
  changeToken: string,
  novaSenha: string,
  confirmacaoSenha: string,
): Promise<ChangePasswordResponse> {
  return apiFetch<ChangePasswordResponse>('/auth/change-password', {
    method: 'POST',
    body: {
      change_token: changeToken,
      nova_senha: novaSenha,
      confirmacao_senha: confirmacaoSenha,
    },
    skipSessionExpired: true,
  });
}

export async function cancelChangePassword(changeToken?: string): Promise<{ ok: boolean }> {
  return apiFetch<{ ok: boolean }>('/auth/cancel-change-password', {
    method: 'POST',
    body: { change_token: changeToken ?? null },
    skipSessionExpired: true,
  });
}

export async function logout(): Promise<{ ok: boolean }> {
  return apiFetch<{ ok: boolean }>('/auth/logout', {
    method: 'POST',
    skipSessionExpired: true,
  });
}

export async function cancelLogin(): Promise<{ ok: boolean }> {
  return apiFetch<{ ok: boolean }>('/auth/cancel-login', {
    method: 'POST',
    skipSessionExpired: true,
  });
}

export async function me(): Promise<MeResponse> {
  return apiFetch<MeResponse>('/auth/me', {
    method: 'GET',
  });
}

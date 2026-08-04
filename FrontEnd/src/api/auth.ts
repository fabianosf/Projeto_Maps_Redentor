import { apiFetch } from './client';
import type {
  ApiErrorBody,
  ChangePasswordSuccess,
  LoginSuccess,
  MeResponse,
} from '../types';

export async function login(matricula: string, senha: string) {
  return apiFetch<LoginSuccess | ApiErrorBody>('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ matricula, senha }),
  });
}

export async function changePassword(
  changeToken: string,
  novaSenha: string,
  confirmacaoSenha: string,
) {
  return apiFetch<ChangePasswordSuccess | ApiErrorBody>('/auth/change-password', {
    method: 'POST',
    body: JSON.stringify({
      change_token: changeToken,
      nova_senha: novaSenha,
      confirmacao_senha: confirmacaoSenha,
    }),
  });
}

export async function cancelChangePassword(changeToken?: string) {
  return apiFetch<{ ok: boolean }>('/auth/cancel-change-password', {
    method: 'POST',
    body: JSON.stringify({ change_token: changeToken ?? null }),
  });
}

export async function logout() {
  return apiFetch<{ ok: boolean }>('/auth/logout', {
    method: 'POST',
  });
}

export async function me() {
  return apiFetch<MeResponse | ApiErrorBody>('/auth/me', {
    method: 'GET',
  });
}

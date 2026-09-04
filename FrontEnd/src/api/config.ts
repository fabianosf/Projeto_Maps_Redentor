import { apiFetch } from './client';
import type { ApiSuccess } from '@/types/api';

export type ConfigLoginResponse = ApiSuccess<{
  chave: string;
  valor: string;
  bloqueio_tentativas: boolean;
  mensagem?: string;
}>;

export async function getQtdTentativas(): Promise<ConfigLoginResponse> {
  return apiFetch<ConfigLoginResponse>('/config/qtd-tentativas', {
    method: 'GET',
  });
}

export async function saveQtdTentativas(
  valor: string,
  bloqueioTentativas: boolean,
): Promise<ConfigLoginResponse> {
  return apiFetch<ConfigLoginResponse>('/config/qtd-tentativas', {
    method: 'PUT',
    body: {
      valor,
      bloqueio_tentativas: bloqueioTentativas,
    },
  });
}

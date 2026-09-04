import { apiFetch } from './client';
import type { ApiErrorBody } from '../types';

export async function getQtdTentativas() {
  return apiFetch<
    | {
        ok: true;
        chave: string;
        valor: string;
        bloqueio_tentativas?: boolean;
      }
    | ApiErrorBody
  >('/config/qtd-tentativas', { method: 'GET' });
}

export async function saveQtdTentativas(valor: string, bloqueioTentativas: boolean) {
  return apiFetch<
    | {
        ok: true;
        chave: string;
        valor: string;
        bloqueio_tentativas?: boolean;
        mensagem?: string;
      }
    | ApiErrorBody
  >('/config/qtd-tentativas', {
    method: 'PUT',
    body: JSON.stringify({ valor, bloqueio_tentativas: bloqueioTentativas }),
  });
}

import { apiFetch } from './client';
import type { ApiErrorBody } from '@/types';

export interface TipoAvaria {
  id_tip: number;
  descricao: string;
}

export async function listTiposAvaria() {
  return apiFetch<{ ok: true; tipos: TipoAvaria[] } | ApiErrorBody>(
    '/mensagem/tipos-avaria',
    { method: 'GET' },
  );
}

export async function enviarMensagem(payload: {
  numero_frota: string;
  id_tip: number;
  texto: string;
}) {
  return apiFetch<
    | { ok: true; mensagem?: string; avaria?: Record<string, unknown> }
    | ApiErrorBody
  >('/mensagem', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

import { apiFetch } from './client';
import type { ApiErrorBody } from '@/types';

export interface GuiaRecord {
  id_guia: number;
  numero: string;
  id_empresa?: number | null;
  id_linha?: number | null;
  id_turno?: number | null;
  id_veiculo?: number | null;
  id_motorista?: number | null;
  numero_frota?: string | null;
  matricula_motorista?: string | null;
  hor_ini?: string | null;
  hor_fim?: string | null;
  roleta01_ini?: number | null;
  roleta01_fim?: number | null;
  roleta2_ini?: number | null;
  roleta2_fim?: number | null;
  observacao?: string | null;
  data?: string | null;
}

export async function getGuiaByNumero(numero: string) {
  return apiFetch<{ ok: true; guia: GuiaRecord } | ApiErrorBody>(
    `/guia/by-numero/${encodeURIComponent(numero)}`,
    { method: 'GET' },
  );
}

export async function createGuia(body: Record<string, unknown>) {
  return apiFetch<
    | { ok: true; guia: GuiaRecord; mensagem?: string }
    | ApiErrorBody
  >('/guia', {
    method: 'POST',
    body: JSON.stringify(body),
  });
}

export async function updateGuia(idGuia: number, body: Record<string, unknown>) {
  return apiFetch<
    | { ok: true; guia: GuiaRecord; mensagem?: string }
    | ApiErrorBody
  >(`/guia/${idGuia}`, {
    method: 'PUT',
    body: JSON.stringify(body),
  });
}

export async function deleteGuia(idGuia: number) {
  return apiFetch<{ ok: true; mensagem?: string } | ApiErrorBody>(
    `/guia/${idGuia}`,
    { method: 'DELETE' },
  );
}

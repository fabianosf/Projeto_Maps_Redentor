import { apiFetch } from './client';
import type {
  Guia,
  GuiaDeleteResponse,
  GuiaPayload,
  GuiaResponse,
} from '@/types/guia';

/** @deprecated Prefer type Guia from @/types/guia */
export type GuiaRecord = Guia;

export async function getGuiaByNumero(numero: string): Promise<GuiaResponse> {
  return apiFetch<GuiaResponse>(`/guia/by-numero/${encodeURIComponent(numero)}`, {
    method: 'GET',
  });
}

export async function createGuia(body: GuiaPayload): Promise<GuiaResponse> {
  return apiFetch<GuiaResponse>('/guia', {
    method: 'POST',
    body,
  });
}

export async function updateGuia(
  idGuia: number,
  body: GuiaPayload,
): Promise<GuiaResponse> {
  return apiFetch<GuiaResponse>(`/guia/${idGuia}`, {
    method: 'PUT',
    body,
  });
}

export async function deleteGuia(idGuia: number): Promise<GuiaDeleteResponse> {
  return apiFetch<GuiaDeleteResponse>(`/guia/${idGuia}`, {
    method: 'DELETE',
  });
}

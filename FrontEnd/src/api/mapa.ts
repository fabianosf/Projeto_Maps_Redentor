import { apiFetch } from './client';
import type {
  ItemMapPayload,
  MapaDeleteResponse,
  MapaHeaderPayload,
  MapaItemResponse,
  MapaOcupacaoResponse,
  MapaResponse,
  MapaViagemResponse,
  MapasListResponse,
  ViagemPayload,
} from '@/types/mapa';

export async function listMapas(params?: {
  data?: string;
}): Promise<MapasListResponse> {
  const q = new URLSearchParams();
  if (params?.data?.trim()) q.set('data', params.data.trim());
  const suffix = q.toString() ? `?${q.toString()}` : '';
  return apiFetch<MapasListResponse>(`/mapas${suffix}`, { method: 'GET' });
}

export async function getMapa(idRegistro: number): Promise<MapaResponse> {
  return apiFetch<MapaResponse>(`/mapas/${idRegistro}`, { method: 'GET' });
}

export async function createMapa(payload: MapaHeaderPayload): Promise<MapaResponse> {
  return apiFetch<MapaResponse>('/mapas', {
    method: 'POST',
    body: payload,
  });
}

export async function updateMapa(
  idRegistro: number,
  payload: MapaHeaderPayload,
): Promise<MapaResponse> {
  return apiFetch<MapaResponse>(`/mapas/${idRegistro}`, {
    method: 'PUT',
    body: payload,
  });
}

export async function deleteMapa(idRegistro: number): Promise<MapaDeleteResponse> {
  return apiFetch<MapaDeleteResponse>(`/mapas/${idRegistro}`, {
    method: 'DELETE',
  });
}

export async function createItem(
  idRegistro: number,
  payload: ItemMapPayload,
): Promise<MapaItemResponse> {
  return apiFetch<MapaItemResponse>(`/mapas/${idRegistro}/itens`, {
    method: 'POST',
    body: payload,
  });
}

export async function updateItem(
  idItem: number,
  payload: ItemMapPayload,
): Promise<MapaItemResponse> {
  return apiFetch<MapaItemResponse>(`/mapas/itens/${idItem}`, {
    method: 'PUT',
    body: payload,
  });
}

export async function deleteItem(idItem: number): Promise<MapaDeleteResponse> {
  return apiFetch<MapaDeleteResponse>(`/mapas/itens/${idItem}`, {
    method: 'DELETE',
  });
}

export async function listOcupacaoEscalas(params?: {
  id_mapa?: number;
  id_empresa?: number;
  id_linha?: number;
  data?: string;
}): Promise<MapaOcupacaoResponse> {
  const q = new URLSearchParams();
  if (params?.id_mapa != null) q.set('id_mapa', String(params.id_mapa));
  if (params?.id_empresa != null) q.set('id_empresa', String(params.id_empresa));
  if (params?.id_linha != null) q.set('id_linha', String(params.id_linha));
  if (params?.data) q.set('data', params.data);
  const suffix = q.toString() ? `?${q.toString()}` : '';
  return apiFetch<MapaOcupacaoResponse>(`/mapas/ocupacao${suffix}`, {
    method: 'GET',
  });
}

export async function darBaixaItem(
  idItem: number,
  payload: {
    fim_real: string;
    motivo_baixa?: string;
    observacao_baixa?: string;
  },
): Promise<MapaItemResponse> {
  return apiFetch<MapaItemResponse>(`/mapas/itens/${idItem}/baixa`, {
    method: 'POST',
    body: payload,
  });
}

export async function createViagem(
  idItem: number,
  payload: ViagemPayload,
): Promise<MapaViagemResponse> {
  return apiFetch<MapaViagemResponse>(`/mapas/itens/${idItem}/viagens`, {
    method: 'POST',
    body: payload,
  });
}

export async function updateViagem(
  idViagem: number,
  payload: ViagemPayload,
): Promise<MapaViagemResponse> {
  return apiFetch<MapaViagemResponse>(`/mapas/viagens/${idViagem}`, {
    method: 'PUT',
    body: payload,
  });
}

export async function deleteViagem(idViagem: number): Promise<MapaDeleteResponse> {
  return apiFetch<MapaDeleteResponse>(`/mapas/viagens/${idViagem}`, {
    method: 'DELETE',
  });
}

import { apiFetch } from './client';
import type {
  ItemMapPayload,
  MapaDeleteResponse,
  MapaHeaderPayload,
  MapaItemResponse,
  MapaResponse,
  MapaViagemResponse,
  MapasListResponse,
  ViagemPayload,
} from '@/types/mapa';

export async function listMapas(): Promise<MapasListResponse> {
  return apiFetch<MapasListResponse>('/mapas', { method: 'GET' });
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

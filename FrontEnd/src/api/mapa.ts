import { apiFetch } from './client';
import type { ApiErrorBody } from '@/types';
import type {
  CadastrosMestres,
  ItemMapPayload,
  MapaCompleto,
  MapaHeaderPayload,
  MapaItem,
  MapaListaItem,
  MapaViagem,
  ViagemPayload,
} from '@/types/mapa';

export async function listMapas() {
  return apiFetch<{ ok: true; mapas: MapaListaItem[] } | ApiErrorBody>('/mapa', {
    method: 'GET',
  });
}

export async function getMapa(idRegistro: number) {
  return apiFetch<{ ok: true; mapa: MapaCompleto } | ApiErrorBody>(`/mapa/${idRegistro}`, {
    method: 'GET',
  });
}

export async function getCadastros() {
  return apiFetch<{ ok: true; cadastros: CadastrosMestres } | ApiErrorBody>(
    '/mapa/cadastros',
    { method: 'GET' },
  );
}

export async function createMapa(payload: MapaHeaderPayload) {
  return apiFetch<{ ok: true; mapa: MapaCompleto } | ApiErrorBody>('/mapa', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function updateMapa(idRegistro: number, payload: MapaHeaderPayload) {
  return apiFetch<{ ok: true; mapa: MapaCompleto } | ApiErrorBody>(
    `/mapa/${idRegistro}`,
    {
      method: 'PUT',
      body: JSON.stringify(payload),
    },
  );
}

export async function deleteMapa(idRegistro: number) {
  return apiFetch<{ ok: true } | ApiErrorBody>(`/mapa/${idRegistro}`, {
    method: 'DELETE',
  });
}

export async function createItem(idRegistro: number, payload: ItemMapPayload) {
  return apiFetch<{ ok: true; item: MapaItem } | ApiErrorBody>(
    `/mapa/${idRegistro}/itens`,
    {
      method: 'POST',
      body: JSON.stringify(payload),
    },
  );
}

export async function updateItem(idItem: number, payload: ItemMapPayload) {
  return apiFetch<{ ok: true; item: MapaItem } | ApiErrorBody>(
    `/mapa/itens/${idItem}`,
    {
      method: 'PUT',
      body: JSON.stringify(payload),
    },
  );
}

export async function deleteItem(idItem: number) {
  return apiFetch<{ ok: true } | ApiErrorBody>(`/mapa/itens/${idItem}`, {
    method: 'DELETE',
  });
}

export async function createViagem(idItem: number, payload: ViagemPayload) {
  return apiFetch<{ ok: true; viagem: MapaViagem } | ApiErrorBody>(
    `/mapa/itens/${idItem}/viagens`,
    {
      method: 'POST',
      body: JSON.stringify(payload),
    },
  );
}

export async function updateViagem(idViagem: number, payload: ViagemPayload) {
  return apiFetch<{ ok: true; viagem: MapaViagem } | ApiErrorBody>(
    `/mapa/viagens/${idViagem}`,
    {
      method: 'PUT',
      body: JSON.stringify(payload),
    },
  );
}

export async function deleteViagem(idViagem: number) {
  return apiFetch<{ ok: true } | ApiErrorBody>(`/mapa/viagens/${idViagem}`, {
    method: 'DELETE',
  });
}

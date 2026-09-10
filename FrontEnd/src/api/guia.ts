import { apiFetch } from './client';
import type {
  Guia,
  GuiaAjusteManualPayload,
  GuiaAlteracaoEscalaPayload,
  GuiaContextoEscala,
  GuiaContextoEscalaResponse,
  GuiaDeleteResponse,
  GuiaEscalasResponse,
  GuiaListResponse,
  GuiaPayload,
  GuiaResponse,
  GuiaRoletaHistoricoItem,
  GuiaRoletaPayload,
  GuiaRoletaResponse,
} from '@/types/guia';

/** @deprecated Prefer type Guia from @/types/guia */
export type GuiaRecord = Guia;

export type ListGuiasFiltros = {
  data?: string;
  sentido?: 'ida' | 'volta' | 'todos';
  origem?: 'roleta' | 'manual' | 'mapa' | 'todos';
  status?: string;
  pendencias?: boolean;
  id_turno?: number;
  id_linha?: number;
};

/** GET /api/v1/guia/consulta — visão consolidada (Mapa + Viagens + Roleta). */
export async function listGuias(
  dataOrFiltros?: string | ListGuiasFiltros,
): Promise<GuiaListResponse> {
  const filtros: ListGuiasFiltros =
    typeof dataOrFiltros === 'string' || dataOrFiltros == null
      ? { data: dataOrFiltros }
      : dataOrFiltros;

  const params = new URLSearchParams();
  if (filtros.data?.trim()) params.set('data', filtros.data.trim());
  if (filtros.sentido && filtros.sentido !== 'todos') {
    params.set('sentido', filtros.sentido);
  }
  if (filtros.origem && filtros.origem !== 'todos') {
    params.set('origem', filtros.origem);
  }
  if (filtros.status?.trim()) params.set('status', filtros.status.trim());
  if (filtros.pendencias) params.set('pendencias', '1');
  if (filtros.id_turno != null) params.set('id_turno', String(filtros.id_turno));
  if (filtros.id_linha != null) params.set('id_linha', String(filtros.id_linha));

  const q = params.toString() ? `?${params.toString()}` : '';
  return apiFetch<GuiaListResponse>(`/guia/consulta${q}`, { method: 'GET' });
}

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

/** Ajuste manual com auditoria — não sobrescreve roleta original. */
export async function registrarAjusteManual(
  idGuia: number,
  body: GuiaAjusteManualPayload,
): Promise<GuiaResponse> {
  return apiFetch<GuiaResponse>(`/guia/${idGuia}/ajuste-manual`, {
    method: 'POST',
    body,
  });
}

/** Salva leitura Ja E / RioCard (ini/fim) por viagem. */
export async function salvarRoletaLeitura(
  body: GuiaRoletaPayload,
): Promise<GuiaRoletaResponse> {
  return apiFetch<GuiaRoletaResponse>('/guia/roletas', {
    method: 'POST',
    body,
  });
}

export async function sugerirRoletaInicial(params: {
  id_veiculo: number;
  fonte: 'jae' | 'riocard';
  sentido: 'ida' | 'volta';
}): Promise<{ ok: boolean; leitura_ini: number | null }> {
  const q = new URLSearchParams({
    id_veiculo: String(params.id_veiculo),
    fonte: params.fonte,
    sentido: params.sentido,
  });
  return apiFetch(`/guia/roletas/sugestao?${q.toString()}`, { method: 'GET' });
}

/** Mapas e escalas do dia para Nova Guia. */
export async function listEscalasGuia(params: {
  data: string;
  id_mapa?: number;
}): Promise<GuiaEscalasResponse> {
  const q = new URLSearchParams({ data: params.data.trim() });
  if (params.id_mapa != null) q.set('id_mapa', String(params.id_mapa));
  return apiFetch<GuiaEscalasResponse>(`/guia/escalas?${q.toString()}`, {
    method: 'GET',
  });
}

export async function getContextoEscala(
  idItem: number,
): Promise<GuiaContextoEscalaResponse> {
  return apiFetch<GuiaContextoEscalaResponse>(
    `/guia/contexto-escala?id_item=${idItem}`,
    { method: 'GET' },
  );
}

export async function registrarAlteracaoEscala(
  idItem: number,
  body: GuiaAlteracaoEscalaPayload,
): Promise<GuiaContextoEscalaResponse> {
  return apiFetch<GuiaContextoEscalaResponse>(
    `/guia/escala/${idItem}/alteracao`,
    { method: 'POST', body },
  );
}

export async function getHistoricoRoleta(
  idLeitura: number,
): Promise<{ ok: boolean; historico: GuiaRoletaHistoricoItem[] }> {
  return apiFetch(`/guia/roletas/${idLeitura}/historico`, { method: 'GET' });
}

export type { GuiaContextoEscala };

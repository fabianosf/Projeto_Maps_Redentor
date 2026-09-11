import { apiFetch } from './client';
import type {
  Guia,
  GuiaAjusteManualPayload,
  GuiaAlteracaoEscalaPayload,
  GuiaAlteracaoRecursoPayload,
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
  GuiaTrechoPayload,
  GuiaTrechoResponse,
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

export async function getGuia(idGuia: number): Promise<GuiaResponse> {
  return apiFetch<GuiaResponse>(`/guia/${idGuia}`, { method: 'GET' });
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

export async function encerrarGuia(
  idGuia: number,
  body?: {
    hor_fim?: string;
    horario_largada?: string;
    motivo_tipo?: 'fim_jornada' | 'transferencia_empresa' | string;
    motivo?: string;
    versao?: number;
  },
): Promise<GuiaResponse> {
  return apiFetch<GuiaResponse>(`/guia/${idGuia}/encerrar`, {
    method: 'POST',
    body: body ?? {},
  });
}

export async function registrarAlteracaoGuia(
  idGuia: number,
  body: GuiaAlteracaoRecursoPayload,
): Promise<GuiaResponse> {
  return apiFetch<GuiaResponse>(`/guia/${idGuia}/alteracao`, {
    method: 'POST',
    body,
  });
}

export async function criarTrechoGuia(
  idGuia: number,
  body: GuiaTrechoPayload,
): Promise<GuiaTrechoResponse> {
  return apiFetch<GuiaTrechoResponse>(`/guia/${idGuia}/trechos`, {
    method: 'POST',
    body,
  });
}

export async function atualizarTrechoGuia(
  idTrecho: number,
  body: GuiaTrechoPayload,
): Promise<GuiaTrechoResponse> {
  return apiFetch<GuiaTrechoResponse>(`/guia/trechos/${idTrecho}`, {
    method: 'PUT',
    body,
  });
}

export async function iniciarTrechoGuia(
  idTrecho: number,
  body?: { hor_ini?: string; versao?: number },
): Promise<GuiaTrechoResponse> {
  return apiFetch<GuiaTrechoResponse>(`/guia/trechos/${idTrecho}/iniciar`, {
    method: 'POST',
    body: body ?? {},
  });
}

export async function concluirTrechoGuia(
  idTrecho: number,
  body?: {
    hor_fim?: string;
    jae_fim?: number | null;
    riocard_fim?: number | null;
    versao?: number;
  },
): Promise<GuiaTrechoResponse> {
  return apiFetch<GuiaTrechoResponse>(`/guia/trechos/${idTrecho}/concluir`, {
    method: 'POST',
    body: body ?? {},
  });
}

export async function cancelarTrechoGuia(
  idTrecho: number,
  body: { motivo: string; versao?: number },
): Promise<GuiaTrechoResponse> {
  return apiFetch<GuiaTrechoResponse>(`/guia/trechos/${idTrecho}/cancelar`, {
    method: 'POST',
    body,
  });
}

export async function excluirTrechoGuia(
  idTrecho: number,
  body?: { versao?: number },
): Promise<{ ok: true; mensagem?: string }> {
  return apiFetch(`/guia/trechos/${idTrecho}`, {
    method: 'DELETE',
    body: body ?? {},
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
  id_guia?: number;
  id_trecho?: number;
}): Promise<{ ok: boolean; leitura_ini: number | null }> {
  const q = new URLSearchParams({
    id_veiculo: String(params.id_veiculo),
    fonte: params.fonte,
    sentido: params.sentido,
  });
  if (params.id_guia != null) q.set('id_guia', String(params.id_guia));
  if (params.id_trecho != null) q.set('id_trecho', String(params.id_trecho));
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

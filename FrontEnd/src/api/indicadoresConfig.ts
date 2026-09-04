import { apiFetch } from './client';
import type {
  IndicadoresCatalogoResponse,
  IndicadoresPermitidosMeResponse,
  IndicadoresSaveResponse,
  IndicadoresVinculoResponse,
  PerfisIndicadoresListResponse,
} from '@/types/indicador';

export async function getIndicadoresCatalogo(): Promise<IndicadoresCatalogoResponse> {
  return apiFetch<IndicadoresCatalogoResponse>('/indicadores-config/indicadores', {
    method: 'GET',
  });
}

export async function getPerfisIndicadores(): Promise<PerfisIndicadoresListResponse> {
  return apiFetch<PerfisIndicadoresListResponse>('/indicadores-config/perfis', {
    method: 'GET',
  });
}

/** RN-08 — só indicadores do perfil da sessão (ignora query manipulada). */
export async function getIndicadoresPermitidosMe(): Promise<IndicadoresPermitidosMeResponse> {
  return apiFetch<IndicadoresPermitidosMeResponse>(
    '/indicadores-config/me/indicadores',
    { method: 'GET' },
  );
}

export async function getIndicadoresPorPerfil(
  idPerfil: number,
): Promise<IndicadoresVinculoResponse> {
  return apiFetch<IndicadoresVinculoResponse>(
    `/indicadores-config/${idPerfil}/indicadores`,
    { method: 'GET' },
  );
}

export async function saveIndicadoresPerfil(
  idPerfil: number,
  idInds: number[],
): Promise<IndicadoresSaveResponse> {
  return apiFetch<IndicadoresSaveResponse>(
    `/indicadores-config/${idPerfil}/indicadores`,
    {
      method: 'PUT',
      body: { id_inds: idInds },
    },
  );
}

/** @deprecated Prefer getPerfisIndicadores */
export const listPerfisIndicadoresConfig = getPerfisIndicadores;
/** @deprecated Prefer getIndicadoresPorPerfil */
export const getIndicadoresVinculoPerfil = getIndicadoresPorPerfil;
/** @deprecated Prefer saveIndicadoresPerfil */
export const saveIndicadoresVinculoPerfil = saveIndicadoresPerfil;

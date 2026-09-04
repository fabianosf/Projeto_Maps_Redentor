import { apiFetch } from './client';
import type { ApiErrorBody } from '../types';
import type {
  IndicadoresCatalogoResponse,
  IndicadoresPermitidosMeResponse,
  IndicadoresSaveResponse,
  IndicadoresVinculoResponse,
  PerfisIndicadoresListResponse,
} from '../types/indicadores';

export async function listIndicadoresCatalogo() {
  return apiFetch<IndicadoresCatalogoResponse | ApiErrorBody>(
    '/indicadores-config/indicadores',
    { method: 'GET' },
  );
}

export async function listPerfisIndicadoresConfig() {
  return apiFetch<PerfisIndicadoresListResponse | ApiErrorBody>(
    '/indicadores-config/perfis',
    { method: 'GET' },
  );
}

export async function getIndicadoresPermitidosMe() {
  return apiFetch<IndicadoresPermitidosMeResponse | ApiErrorBody>(
    '/indicadores-config/me/indicadores',
    { method: 'GET' },
  );
}

export async function getIndicadoresVinculoPerfil(idPerfil: number) {
  return apiFetch<IndicadoresVinculoResponse | ApiErrorBody>(
    `/indicadores-config/${idPerfil}/indicadores`,
    { method: 'GET' },
  );
}

export async function saveIndicadoresVinculoPerfil(
  idPerfil: number,
  idInds: number[],
) {
  return apiFetch<IndicadoresSaveResponse | ApiErrorBody>(
    `/indicadores-config/${idPerfil}/indicadores`,
    {
      method: 'PUT',
      body: JSON.stringify({ id_inds: idInds }),
    },
  );
}

import type { ApiSuccess } from './api';

export interface Indicador {
  id_ind: number;
  cod_ind: number;
  descricao: string;
  detalhe?: string | null;
}

export interface IndicadorVinculo extends Indicador {
  vinculado: boolean;
}

export interface IndicadorPermitido {
  id_ind: number;
  cod_ind: number;
  descricao: string;
  detalhe?: string | null;
}

export type IndicadoresCatalogoResponse = ApiSuccess<{ indicadores: Indicador[] }>;

export type PerfisIndicadoresListResponse = ApiSuccess<{
  perfis: Array<{
    id_perfil: number;
    codigo_perfil: number;
    descricao: string;
  }>;
}>;

export type IndicadoresVinculoResponse = ApiSuccess<{ indicadores: IndicadorVinculo[] }>;

export type IndicadoresSaveResponse = ApiSuccess<{ mensagem: string }>;

export type IndicadoresPermitidosMeResponse = ApiSuccess<{
  indicadores: IndicadorPermitido[];
}>;

/** Aliases usados pelas telas legadas (migração). */
export type IndicadorVinculoItem = IndicadorVinculo;
export type IndicadorPermitidoItem = IndicadorPermitido;

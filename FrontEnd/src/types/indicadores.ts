export type IndicadorVinculoItem = {
  id_ind: number;
  cod_ind: number;
  descricao: string;
  detalhe?: string | null;
  vinculado: boolean;
};

export type IndicadoresCatalogoResponse = {
  ok: true;
  indicadores: Array<{
    id_ind: number;
    cod_ind: number;
    descricao: string;
    detalhe?: string | null;
  }>;
};

export type PerfisIndicadoresListResponse = {
  ok: true;
  perfis: Array<{
    id_perfil: number;
    codigo_perfil: number;
    descricao: string;
  }>;
};

export type IndicadoresVinculoResponse = {
  ok: true;
  indicadores: IndicadorVinculoItem[];
};

export type IndicadoresSaveResponse = {
  ok: true;
  mensagem: string;
};

export type IndicadorPermitidoItem = {
  id_ind: number;
  cod_ind: number;
  descricao: string;
  detalhe?: string | null;
};

export type IndicadoresPermitidosMeResponse = {
  ok: true;
  indicadores: IndicadorPermitidoItem[];
};

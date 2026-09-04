import type { ApiSuccess } from './api';

export interface LinhaEntradaSaida {
  id_linha: number;
  codigo_linha?: number;
  descricao: string;
  id_local_origem?: number;
  id_local_destino?: number;
  codigo_origem?: number;
  descricao_origem?: string;
  codigo_destino?: number;
  descricao_destino?: string;
}

export interface LocalEntradaSaida {
  id_local: number;
  codigo_local?: number;
  descricao: string;
}

/** GET /entrada-saida/contexto — linhas já filtradas pelo local do usuário. */
export type EntradaSaidaContextoResponse = ApiSuccess<{
  id_local_usuario: number | null;
  local_usuario: LocalEntradaSaida | null;
  linhas: LinhaEntradaSaida[];
  locais: LocalEntradaSaida[];
}>;

export type LinhasSaidaResponse = ApiSuccess<{ linhas: LinhaEntradaSaida[] }>;

/** POST /entrada-saida/registrar — id_guia é resolvido só no backend. */
export interface EntradaSaidaRegistrarRequest {
  evento: 'C' | 'S';
  id_linha: number;
  carro: string;
  horario: string;
  temperatura?: string;
  roleta?: string;
  /** Alias aceito pelo service: linha_destino / id_linha_destino */
  id_linha_destino?: number;
  linha_destino?: number;
  /** Alias aceito: destino / id_destino */
  id_destino?: number;
  destino?: number;
}

export type EntradaSaidaRegistrarResponse = ApiSuccess<{
  mensagem?: string;
  evento?: string;
  id_linha?: number;
  id_guia?: number | null;
}>;

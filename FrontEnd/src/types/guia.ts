import type { ApiSuccess } from './api';

/** Registro retornado por GET/POST/PUT /api/v1/guia (tb_guia + joins). */
export interface Guia {
  id_guia: number;
  numero: string;
  id_empresa?: number | null;
  id_linha?: number | null;
  id_turno?: number | null;
  id_veiculo?: number | null;
  id_motorista?: number | null;
  numero_frota?: string | null;
  matricula_motorista?: string | null;
  /** DATETIME no banco; front usa HH:MM extraído. */
  hor_ini?: string | null;
  hor_fim?: string | null;
  roleta01_ini?: number | null;
  roleta01_fim?: number | null;
  roleta2_ini?: number | null;
  roleta2_fim?: number | null;
  observacao?: string | null;
  /** DATETIME do cadastro (tb_guia.data). */
  data?: string | null;
}

/** Body aceito por criar_guia / atualizar_guia (_validar_payload). */
export interface GuiaPayload {
  numero: string;
  /** dd/mm/aaaa */
  data: string;
  id_empresa?: number | null;
  id_linha?: number | null;
  id_turno?: number | null;
  id_veiculo?: number | null;
  id_motorista?: number | null;
  carro?: string;
  motorista?: string;
  numero_frota?: string;
  matricula_motorista?: string;
  hor_ini?: string;
  hor_fim?: string;
  horario_pegada?: string;
  horario_largada?: string;
  roleta01_ini?: number | null;
  roleta01_fim?: number | null;
  roleta01_inicial?: number | null;
  roleta01_final?: number | null;
  roleta2_ini?: number | null;
  roleta2_fim?: number | null;
  roleta2_inicial?: number | null;
  roleta2_final?: number | null;
  observacao?: string;
}

export type GuiaResponse = ApiSuccess<{ guia: Guia; mensagem?: string }>;
export type GuiaDeleteResponse = ApiSuccess<{ mensagem?: string }>;

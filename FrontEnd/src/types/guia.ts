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
  id_item_map?: number | null;
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
  /** Joins aditivos (listagem / by-numero). */
  turno_descricao?: string | null;
  linha_codigo?: string | null;
  linha_descricao?: string | null;
}

export type GuiaSyncStatus =
  | 'sincronizado'
  | 'atualizando'
  | 'pendente'
  | 'divergencia'
  | 'falha'
  | 'manual';

export type SentidoViagem = 'ida' | 'volta';
export type OrigemEmbarque = 'roleta' | 'manual' | 'mapa';

export type GuiaFonteRoleta = 'jae' | 'riocard';

export interface GuiaRoletaBloco {
  leitura_ini?: number | null;
  leitura_fim?: number | null;
  passageiros?: number | null;
  status_leitura?: 'iniciada' | 'finalizada' | null;
  virada?: boolean;
  justificativa_virada?: string | null;
  id_leitura?: number | null;
  id_usuario?: number | null;
  nome_usuario?: string | null;
  atualizado_em?: string | null;
  sugestao_ini?: number | null;
}

export interface GuiaViagemCard {
  key: string;
  viagem_label: string;
  id_viagem?: number | null;
  id_guia?: number | null;
  id_mapa?: number | null;
  cod_map?: number | null;
  codigo_mapa?: string | null;
  mapa?: string | null;
  veiculo: string;
  numero_frota?: string | null;
  id_veiculo?: number | null;
  motorista?: string | null;
  matricula_motorista?: string | null;
  /** Usuário que registrou leitura (Ja E / RioCard). */
  responsavel?: string | null;
  ocorrencias?: string | null;
  observacao?: string | null;
  data: string;
  turno?: string | null;
  sentido: SentidoViagem;
  horario: string;
  horario_saida?: string | null;
  horario_chegada?: string | null;
  embarques: number;
  embarques_roleta?: number | null;
  embarques_previsto_mapa?: number | null;
  origem: OrigemEmbarque;
  status: GuiaSyncStatus;
  roleta?: {
    ini?: number | null;
    fim?: number | null;
    fonte?: string | null;
  } | null;
  ajuste?: {
    embarques: number;
    em: string;
    justificativa?: string;
  } | null;
  jae?: GuiaRoletaBloco | null;
  riocard?: GuiaRoletaBloco | null;
}

export interface GuiaResumoDia {
  titulo_mapa: string;
  turno?: string | null;
  cod_map?: number | null;
  codigo_mapa?: string | null;
  id_registro?: number | null;
  ida: { jae: number; riocard: number };
  volta: { jae: number; riocard: number };
  /** Compat legado — não soma Ja E + RioCard. */
  embarques_ida?: number;
  embarques_volta?: number;
  total_viagens: number;
  ultima_leitura?: string | null;
}

/** Contrato consolidado GET /api/v1/guia e /consulta. */
export type GuiaListResponse = ApiSuccess<{
  data: string;
  status: GuiaSyncStatus;
  resumo: GuiaResumoDia;
  viagens: GuiaViagemCard[];
  guias: Guia[];
  erro_integracao?: string;
}>;

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
  /** Escala de origem (tb_item_map) — preenche vínculos no backend. */
  id_item_map?: number | null;
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
  /** Passageiros executados IDA/VOLTA (persistidos na observação). */
  pas_ida?: number | null;
  pas_volta?: number | null;
  viagens_ida?: number | null;
  viagens_volta?: number | null;
  ocorrencias?: string;
  observacao?: string;
}

export type GuiaAjusteManualPayload = {
  sentido: SentidoViagem;
  embarques: number;
  justificativa: string;
};

export type GuiaViagemPrevista = {
  id_viagem?: number | null;
  horario_saida?: string | null;
  horario_chegada?: string | null;
  placa?: string | null;
  qtd_pas_ida?: number | null;
  qtd_pas_volta?: number | null;
};

/** Contexto readonly da escala (Mapa) para Nova Guia. */
export type GuiaContextoEscala = {
  id_item: number;
  id_mapa?: number | null;
  cod_map?: number | null;
  codigo_mapa?: string | null;
  data?: string | null;
  id_empresa?: number | null;
  empresa?: string | null;
  id_linha?: number | null;
  linha?: string | null;
  codigo_linha?: string | number | null;
  id_turno?: number | null;
  turno?: string | null;
  id_veiculo?: number | null;
  numero_frota?: string | null;
  id_motorista?: number | null;
  matricula_motorista?: string | null;
  motorista?: string | null;
  chegada_ponto?: string | null;
  chegada_ponto_hhmm?: string | null;
  hor_ini_jor?: string | null;
  hor_ini_jor_hhmm?: string | null;
  hor_fim_jor?: string | null;
  hor_fim_jor_hhmm?: string | null;
  status_escala?: string | null;
  viagens_previstas?: GuiaViagemPrevista[];
};

export type GuiaEscalaOpcao = {
  id_item: number;
  id_mapa: number;
  cod_map?: number | null;
  codigo_mapa?: string | null;
  id_turno?: number | null;
  turno?: string | null;
  numero_frota?: string | null;
  matricula_motorista?: string | null;
  motorista?: string | null;
  codigo_linha?: string | number | null;
  linha?: string | null;
  status_escala?: string | null;
  label: string;
};

export type GuiaMapaOpcao = {
  id_registro: number;
  cod_map?: number | null;
  codigo_mapa?: string | null;
  id_turno?: number | null;
  turno?: string | null;
  data?: string | null;
  label: string;
};

export type GuiaEscalasResponse = ApiSuccess<{
  data: string;
  mapas: GuiaMapaOpcao[];
  escalas: GuiaEscalaOpcao[];
}>;

export type GuiaContextoEscalaResponse = ApiSuccess<{
  contexto: GuiaContextoEscala;
  mensagem?: string;
}>;

export type GuiaAlteracaoEscalaPayload = {
  justificativa: string;
  numero_frota?: string;
  carro?: string;
  matricula_motorista?: string;
  motorista?: string;
  hor_ini_jor?: string;
  hor_fim_jor?: string;
  chegada_ponto?: string;
};

export type GuiaRoletaHistoricoItem = {
  id_historico?: number;
  id_leitura?: number;
  acao?: string;
  leitura_ini?: number | null;
  leitura_fim?: number | null;
  passageiros?: number | null;
  virada?: number | boolean | null;
  justificativa?: string | null;
  id_usuario?: number | null;
  matricula_usuario?: string | null;
  nome_usuario?: string | null;
  registrado_em?: string | null;
};

export type GuiaRoletaPayload = {
  id_viagem?: number | null;
  id_guia?: number | null;
  id_veiculo?: number | null;
  sentido: SentidoViagem;
  fonte: GuiaFonteRoleta;
  leitura_ini?: number | null;
  leitura_fim?: number | null;
  justificativa_virada?: string;
  usar_sugestao?: boolean;
};

export type GuiaRoletaResponse = ApiSuccess<{
  leitura: GuiaRoletaBloco & {
    id_leitura: number;
    sentido: SentidoViagem;
    fonte: GuiaFonteRoleta;
    status_leitura: string;
  };
  mensagem?: string;
}>;

export type GuiaResponse = ApiSuccess<{ guia: Guia; mensagem?: string }>;
export type GuiaDeleteResponse = ApiSuccess<{ mensagem?: string }>;

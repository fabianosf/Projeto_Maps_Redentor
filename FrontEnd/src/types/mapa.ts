import type { ApiSuccess } from './api';

export interface MapaListaItem {
  id_registro: number;
  cod_map: number;
  data: string;
  empresa?: string | null;
  linha?: string | null;
  turno: string;
  despachante?: string;
}

export interface MapaViagem {
  id_viagem: number;
  /** FK tb_item_map.id_item — viagens pertencem ao item (escala), não só ao veículo. */
  id_item_registro: number;
  /** Alias explícito do item (mesmo valor de id_item_registro). */
  id_mapa_item?: number;
  horario_saida: string;
  horario_chegada: string;
  /** HH:MM — coluna tb_viagem.placa (campo Placa da UI) */
  placa?: string | null;
  intervalo?: number | null;
  qtd_pas_ida: number;
  qtd_pas_volta: number;
}

export interface MapaItem {
  id_item: number;
  /** Alias de id_item para deixá-lo explícito na UI/API. */
  id_mapa_item?: number;
  idmap: number;
  id_linha: number;
  id_veiculo: number;
  id_motorista: number | null;
  hor_ini_jor: string | null;
  hor_fim_jor: string | null;
  chegada_ponto: string | null;
  /** EM_ANDAMENTO | ENCERRADA */
  status_escala?: 'EM_ANDAMENTO' | 'ENCERRADA' | string;
  baixa_em?: string | null;
  /** Planejado (aliases de hor_ini_jor / hor_fim_jor). */
  inicio_jornada_planejado?: string | null;
  fim_jornada_planejado?: string | null;
  inicio_real?: string | null;
  fim_real?: string | null;
  motivo_baixa?: string | null;
  observacao_baixa?: string | null;
  duracao_trabalhada_minutos?: number | null;
  duracao_trabalhada_hhmm?: string | null;
  id_empresa?: number;
  empresa?: string;
  linha?: string;
  codigo_linha?: number | string;
  numero_frota?: string;
  placa?: string;
  motorista?: string;
  matricula_motorista?: string;
  viagens: MapaViagem[];
}

export interface MapaOcupacaoVeiculo {
  id_veiculo: number;
  prefixo?: string;
  numero_frota?: string;
  id_mapa_item?: number;
  id_item?: number;
  id_mapa?: number;
  idmap?: number;
  cod_map?: number | null;
  id_motorista?: number | null;
  matricula_motorista?: string | null;
  nome_motorista?: string | null;
  inicio_real?: string | null;
  status?: string;
  status_escala?: string;
}

export interface MapaOcupacaoMotorista {
  id_motorista: number;
  matricula?: string | null;
  nome?: string | null;
  id_mapa_item?: number;
  id_item?: number;
  id_mapa?: number;
  idmap?: number;
  cod_map?: number | null;
  id_veiculo?: number;
  prefixo_veiculo?: string;
  numero_frota?: string;
  inicio_real?: string | null;
  status?: string;
  status_escala?: string;
}

export type MapaOcupacaoResponse = ApiSuccess<{
  veiculos_ocupados: MapaOcupacaoVeiculo[];
  motoristas_ocupados: MapaOcupacaoMotorista[];
  /** Aliases legados */
  veiculos?: MapaOcupacaoVeiculo[];
  motoristas?: MapaOcupacaoMotorista[];
}>;

export interface MapaCompleto {
  id_registro: number;
  cod_map: number;
  id_usuario: number;
  /** Legado — novos MAPAs podem vir null. */
  id_linha?: number | null;
  id_turno: number;
  data: string;
  inicio_jornada_des: string;
  fim_jornada_des: string | null;
  observacao?: string | null;
  linha?: string | null;
  id_empresa?: number | null;
  empresa?: string | null;
  turno: string;
  despachante: string;
  matricula_despachante?: string;
  itens: MapaItem[];
}

/** Cabeçalho: empresa/linha/veículo deixam de ser obrigatórios (fase API). */
export interface MapaHeaderPayload {
  id_turno: number;
  codigo_turno?: number | null;
  turno?: string | null;
  data: string;
  inicio_jornada_des: string;
  fim_jornada_des?: string | null;
  observacao?: string | null;
  /** @deprecated — mover para item; UI ainda envia até fase de tela. */
  id_linha?: number | null;
  codigo_linha?: string | number | null;
  id_empresa?: number | null;
  empresa?: string | null;
  numero_frota?: string;
}

export interface ItemMapPayload {
  id_linha?: number;
  id_veiculo?: number;
  id_motorista?: number;
  /** Número do carro em tb_veiculo.numero_frota */
  numero_frota?: string;
  /** Matrícula em tb_motorista.matricula */
  matricula?: string;
  hor_ini_jor?: string | null;
  hor_fim_jor?: string | null;
  chegada_ponto?: string | null;
}

export interface ViagemPayload {
  horario_saida: string;
  horario_chegada: string;
  /** Obrigatório ao criar viagem (POST); vínculo ao item/escala, não à frota. */
  id_mapa_item?: number;
  id_item?: number;
  /** HH:MM — coluna tb_viagem.placa */
  placa?: string | null;
  intervalo?: number | null;
  qtd_pas_ida?: number;
  qtd_pas_volta?: number;
  qtd_passageiro?: number;
}

export type MapasListResponse = ApiSuccess<{ mapas: MapaListaItem[] }>;
export type MapaResponse = ApiSuccess<{ mapa: MapaCompleto }>;
export type MapaItemResponse = ApiSuccess<{ item: MapaItem }>;
export type MapaViagemResponse = ApiSuccess<{ viagem: MapaViagem }>;
export type MapaDeleteResponse = ApiSuccess;

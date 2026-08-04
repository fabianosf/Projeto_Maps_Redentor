export interface MapaListaItem {
  id_registro: number;
  cod_map: number;
  data: string;
  empresa: string;
  linha: string;
  turno: string;
  despachante?: string;
}

export interface MapaViagem {
  id_viagem: number;
  id_item_registro: number;
  horario_saida: string;
  horario_chegada: string;
  /** Horário HH:MM do campo Placa da UI (tb_viagem.placa) */
  placa?: string | null;
  intervalo?: number | null;
  qtd_pas_ida: number;
  qtd_pas_volta: number;
}

export interface MapaItem {
  id_item: number;
  idmap: number;
  id_veiculo: number;
  id_motorista: number;
  hor_ini_jor: string | null;
  hor_fim_jor: string | null;
  chegada_ponto: string | null;
  numero_frota?: string;
  placa?: string;
  motorista?: string;
  matricula_motorista?: string;
  viagens: MapaViagem[];
}

export interface MapaCompleto {
  id_registro: number;
  cod_map: number;
  id_usuario: number;
  id_linha: number;
  id_turno: number;
  data: string;
  inicio_jornada_des: string;
  fim_jornada_des: string;
  observacao?: string | null;
  linha: string;
  empresa: string;
  turno: string;
  despachante: string;
  matricula_despachante?: string;
  itens: MapaItem[];
}

export interface EmpresaCadastro {
  id_empresa: number;
  codigo_empresa?: number;
  descricao: string;
  ativo?: number;
}

export interface LinhaCadastro {
  id_linha: number;
  codigo_linha?: number;
  id_empresa: number;
  descricao: string;
  empresa?: string;
  ativo?: number;
}

export interface TurnoCadastro {
  id_turno: number;
  codigo_turno?: number;
  descricao: string;
  ativo?: number;
}

export interface VeiculoCadastro {
  id_veiculo: number;
  codigo_veiculo?: number;
  numero_frota: string;
  placa?: string;
  ativo?: number;
}

export interface MotoristaCadastro {
  id_motorista: number;
  matricula: string;
  nome: string;
  ativo?: number;
}

export interface CadastrosMestres {
  empresas: EmpresaCadastro[];
  linhas: LinhaCadastro[];
  turnos: TurnoCadastro[];
  veiculos: VeiculoCadastro[];
  motoristas: MotoristaCadastro[];
}

export interface MapaHeaderPayload {
  id_linha?: number | null;
  codigo_linha?: string | number | null;
  id_empresa?: number | null;
  id_turno: number;
  codigo_turno?: number | null;
  turno?: string | null;
  data: string;
  inicio_jornada_des: string;
  fim_jornada_des?: string | null;
  observacao?: string | null;
}

export interface ItemMapPayload {
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
  /** HH:MM — coluna tb_viagem.placa (campo Placa da tela) */
  placa?: string | null;
  intervalo?: number | null;
  qtd_pas_ida?: number;
  qtd_pas_volta?: number;
  /** Atalho de UI — gravado em qtd_pas_ida */
  qtd_passageiro?: number;
}

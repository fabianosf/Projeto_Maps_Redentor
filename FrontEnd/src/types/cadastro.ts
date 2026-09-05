import type { ApiSuccess } from './api';

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

export interface LocalCadastro {
  id_local: number;
  codigo_local: number;
  descricao: string;
  ativo?: number;
}

export interface VeiculoCadastro {
  id_veiculo: number;
  codigo_veiculo?: number;
  numero_frota: string;
  placa?: string;
  id_empresa?: number;
  ativo?: number;
}

export interface MotoristaCadastro {
  id_motorista: number;
  matricula: string;
  nome?: string;
  ativo?: number;
}

export interface CadastrosMestres {
  empresas: EmpresaCadastro[];
  linhas: LinhaCadastro[];
  turnos: TurnoCadastro[];
  locais: LocalCadastro[];
  veiculos: VeiculoCadastro[];
  motoristas: MotoristaCadastro[];
}

export type CadastrosResponse = ApiSuccess<{ cadastros: CadastrosMestres }>;

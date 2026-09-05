import type { ApiSuccess } from './api';

/** Códigos de perfil alinhados ao BackEnd (constants.py). */
export type CodigoPerfil = 1 | 2 | 3;

/** Dados públicos do usuário autenticado (sem senha). */
export interface UsuarioPublico {
  id_usuario: number;
  matricula: string;
  nome: string;
  codigo_perfil: CodigoPerfil;
  trocar_senha: boolean;
}

/** Item de listagem GET /users. */
export interface UsuarioLista {
  id_usuario: number;
  matricula: string;
  nome: string;
  ativo: boolean | number;
  trocar_senha: boolean | number;
  id_perfil?: number;
  codigo_perfil: CodigoPerfil | number;
  perfil_descricao?: string;
  id_empresa?: number | null;
  id_turno?: number | null;
  id_local?: number | null;
  foto_base64?: string | null;
  foto_mime?: string | null;
  /** Presente só na resposta de create/reset — nunca logar. */
  senha_temporaria?: string;
}

export interface ErpFuncionario {
  cod_func: string;
  nome: string;
  foto_base64?: string | null;
  foto_mime?: string | null;
}

export interface PerfilItem {
  id_perfil: number;
  codigo_perfil: number;
  descricao: string;
}

export type UsersListResponse = ApiSuccess<{ usuarios: UsuarioLista[] }>;
export type UserMutationResponse = ApiSuccess<{
  usuario: UsuarioLista;
  mensagem?: string;
  reativado?: boolean;
  /** Presente na reativação (também em usuario.senha_temporaria). */
  senha_temporaria?: string;
}>;
export type PerfisListResponse = ApiSuccess<{ perfis: PerfilItem[] }>;
export type ErpFuncionarioResponse = ApiSuccess<{ funcionario: ErpFuncionario }>;

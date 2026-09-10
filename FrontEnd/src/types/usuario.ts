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
  foto_url?: string | null;
  foto_base64?: string | null;
  foto_mime?: string | null;
  /** Presente só na resposta de create/reset — nunca logar. */
  senha_temporaria?: string;
}

/** Prefill quando a matrícula existe no RH mas ainda não em tb_usuario. */
export interface UsuarioPrefillRh {
  matricula: string;
  nome: string;
  foto_url?: string | null;
  origem?: 'oracle' | 'mock' | string;
  ativo?: boolean;
  id_usuario?: number;
  codigo_perfil?: CodigoPerfil | number;
  id_empresa?: number | null;
  id_turno?: number | null;
  id_local?: number | null;
}

export interface ErpFuncionario {
  matricula: string;
  nome: string;
  foto_url?: string | null;
  ativo: boolean;
  origem: 'oracle' | 'mock';
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
/** GET /users/by-matricula/:matricula — Oracle/RH primeiro. */
export type UserByMatriculaResponse = ApiSuccess<{
  ja_cadastrado: boolean;
  usuario: UsuarioLista | UsuarioPrefillRh;
  mensagem?: string;
  /** oracle | mock — origem da consulta RH (não é tb_usuario). */
  fonte_rh?: string;
}>;
export type PerfisListResponse = ApiSuccess<{ perfis: PerfilItem[] }>;

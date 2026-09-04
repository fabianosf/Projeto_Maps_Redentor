import type { ApiSuccess } from './api';
import type { CodigoPerfil, UsuarioPublico } from './usuario';

/** Sessão exposta ao React — nunca inclui senha, token ou cookie. */
export interface AuthSession {
  matricula: string;
  nome: string;
  codigo_perfil: CodigoPerfil;
  permissoes: readonly string[];
}

export type Permissao =
  | 'principal'
  | 'usuarios'
  | 'guia'
  | 'entrada-saida'
  | 'configuracao'
  | 'indicadores'
  | 'mapas'
  | 'reset_senha';

export interface LoginRequest {
  matricula: string;
  senha: string;
}

export type LoginResponse = ApiSuccess<{
  trocar_senha: boolean;
  change_token?: string;
  usuario: UsuarioPublico;
}>;

export type ChangePasswordResponse = ApiSuccess<{
  mensagem: string;
}>;

export type MeResponse = ApiSuccess<{
  usuario: UsuarioPublico;
  sessao: {
    matricula: string;
    codigo_perfil: CodigoPerfil;
  };
}>;

export type LogoutResponse = ApiSuccess<{ mensagem?: string }> | { ok: boolean };

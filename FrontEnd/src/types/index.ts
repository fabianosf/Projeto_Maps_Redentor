export type CodigoPerfil = 1 | 2;

export interface UsuarioPublico {
  id_usuario: number;
  matricula: string;
  nome: string;
  codigo_perfil: CodigoPerfil;
  trocar_senha: boolean;
}

export interface ApiErrorBody {
  ok: false;
  mensagem: string;
  codigo?: string;
}

export interface LoginSuccess {
  ok: true;
  trocar_senha: boolean;
  change_token?: string;
  usuario: UsuarioPublico;
}

export interface ChangePasswordSuccess {
  ok: true;
  mensagem: string;
}

export interface MeResponse {
  ok: true;
  usuario: UsuarioPublico;
  sessao: {
    matricula: string;
    codigo_perfil: CodigoPerfil;
  };
}

/** Item de GET /api/v1/users */
export interface UsuarioLista {
  id_usuario: number;
  matricula: string;
  nome: string;
  ativo: boolean | number;
  trocar_senha: boolean | number;
  id_perfil?: number;
  codigo_perfil: CodigoPerfil | number;
  perfil_descricao?: string;
}

export interface UsersListResponse {
  ok: true;
  usuarios: UsuarioLista[];
}

export interface UserMutationResponse {
  ok: true;
  usuario: UsuarioLista;
  mensagem?: string;
}

export interface PerfilItem {
  id_perfil: number;
  codigo_perfil: number;
  descricao: string;
}

export interface PerfisListResponse {
  ok: true;
  perfis: PerfilItem[];
}

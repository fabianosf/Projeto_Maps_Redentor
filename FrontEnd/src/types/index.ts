export type CodigoPerfil = 1 | 2 | 3;

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
  id_empresa?: number | null;
  id_turno?: number | null;
  id_local?: number | null;
  foto_base64?: string | null;
  foto_mime?: string | null;
}

/** Funcionário retornado pelo ERP Oracle (GET /users/erp-funcionario) */
export interface ErpFuncionario {
  cod_func: string;
  nome: string;
  foto_base64?: string | null;
  foto_mime?: string | null;
}

export interface ErpFuncionarioResponse {
  ok: true;
  funcionario: ErpFuncionario;
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

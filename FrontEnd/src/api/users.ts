import { apiFetch } from './client';
import type {
  ErpFuncionarioResponse,
  PerfisListResponse,
  UserMutationResponse,
  UsersListResponse,
} from '@/types';

export type UsuarioVinculos = {
  id_empresa?: number | null;
  id_turno?: number | null;
  id_local?: number | null;
};

export async function listUsers(): Promise<UsersListResponse> {
  return apiFetch<UsersListResponse>('/users', { method: 'GET' });
}

export async function listPerfis(): Promise<PerfisListResponse> {
  return apiFetch<PerfisListResponse>('/users/perfis', { method: 'GET' });
}

export async function getUserByMatricula(matricula: string): Promise<UserMutationResponse> {
  return apiFetch<UserMutationResponse>(
    `/users/by-matricula/${encodeURIComponent(matricula)}`,
    { method: 'GET' },
  );
}

export async function getErpFuncionario(matricula: string): Promise<ErpFuncionarioResponse> {
  return apiFetch<ErpFuncionarioResponse>(
    `/users/erp-funcionario/${encodeURIComponent(matricula)}`,
    { method: 'GET' },
  );
}

export async function createUser(
  matricula: string,
  nome: string,
  codigoPerfil: number,
  vinculos?: UsuarioVinculos,
): Promise<UserMutationResponse> {
  return apiFetch<UserMutationResponse>('/users', {
    method: 'POST',
    body: {
      matricula,
      nome,
      codigo_perfil: codigoPerfil,
      id_empresa: vinculos?.id_empresa ?? null,
      id_turno: vinculos?.id_turno ?? null,
      id_local: vinculos?.id_local ?? null,
    },
  });
}

export async function updateUserProfile(
  idUsuario: number,
  codigoPerfil: number,
  nome?: string,
  vinculos?: UsuarioVinculos,
): Promise<UserMutationResponse> {
  return apiFetch<UserMutationResponse>(`/users/${idUsuario}`, {
    method: 'PUT',
    body: {
      codigo_perfil: codigoPerfil,
      ...(nome !== undefined ? { nome } : {}),
      id_empresa: vinculos?.id_empresa ?? null,
      id_turno: vinculos?.id_turno ?? null,
      id_local: vinculos?.id_local ?? null,
    },
  });
}

export async function deleteUser(
  idUsuario: number,
): Promise<{ ok: boolean; mensagem?: string }> {
  return apiFetch<{ ok: boolean; mensagem?: string }>(`/users/${idUsuario}`, {
    method: 'DELETE',
  });
}

export async function resetUserPassword(
  idUsuario: number,
): Promise<UserMutationResponse> {
  return apiFetch<UserMutationResponse>(`/users/${idUsuario}/reset-password`, {
    method: 'POST',
  });
}

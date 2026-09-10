import { apiFetch } from './client';
import type {
  ErpFuncionario,
  PerfisListResponse,
  UserByMatriculaResponse,
  UserMutationResponse,
  UsersListResponse,
} from '@/types';

export type UsuarioVinculos = {
  id_empresa?: number | null;
  id_turno?: number | null;
  id_local?: number | null;
};

function idVinculoOuNull(valor: number | null | undefined): number | null {
  if (valor == null) return null;
  const n = Number(valor);
  if (!Number.isInteger(n) || n <= 0) return null;
  return n;
}

export async function listUsers(): Promise<UsersListResponse> {
  return apiFetch<UsersListResponse>('/users', { method: 'GET' });
}

export async function listPerfis(): Promise<PerfisListResponse> {
  return apiFetch<PerfisListResponse>('/users/perfis', { method: 'GET' });
}

export async function getUserByMatricula(
  matricula: string,
): Promise<UserByMatriculaResponse> {
  return apiFetch<UserByMatriculaResponse>(
    `/users/by-matricula/${encodeURIComponent(matricula)}`,
    { method: 'GET' },
  );
}

export async function getErpFuncionario(matricula: string): Promise<ErpFuncionario> {
  return apiFetch<ErpFuncionario>(`/users/erp-funcionario/${encodeURIComponent(matricula)}`, {
    method: 'GET',
  });
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
      codigo_perfil: Number(codigoPerfil),
      id_empresa: idVinculoOuNull(vinculos?.id_empresa),
      id_turno: idVinculoOuNull(vinculos?.id_turno),
      id_local: idVinculoOuNull(vinculos?.id_local),
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
      codigo_perfil: Number(codigoPerfil),
      ...(nome !== undefined ? { nome } : {}),
      id_empresa: idVinculoOuNull(vinculos?.id_empresa),
      id_turno: idVinculoOuNull(vinculos?.id_turno),
      id_local: idVinculoOuNull(vinculos?.id_local),
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

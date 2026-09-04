import { apiFetch } from './client';
import type {
  ApiErrorBody,
  ErpFuncionarioResponse,
  PerfisListResponse,
  UserMutationResponse,
  UsersListResponse,
} from '../types';

export type UsuarioVinculos = {
  id_empresa?: number | null;
  id_turno?: number | null;
  id_local?: number | null;
};

export async function listUsers() {
  return apiFetch<UsersListResponse | ApiErrorBody>('/users', {
    method: 'GET',
  });
}

export async function listPerfis() {
  return apiFetch<PerfisListResponse | ApiErrorBody>('/users/perfis', {
    method: 'GET',
  });
}

export async function getUserByMatricula(matricula: string) {
  return apiFetch<UserMutationResponse | ApiErrorBody>(
    `/users/by-matricula/${encodeURIComponent(matricula)}`,
    { method: 'GET' },
  );
}

export async function getErpFuncionario(matricula: string) {
  return apiFetch<ErpFuncionarioResponse | ApiErrorBody>(
    `/users/erp-funcionario/${encodeURIComponent(matricula)}`,
    { method: 'GET' },
  );
}

export async function createUser(
  matricula: string,
  nome: string,
  codigoPerfil: number,
  vinculos?: UsuarioVinculos,
) {
  return apiFetch<UserMutationResponse | ApiErrorBody>('/users', {
    method: 'POST',
    body: JSON.stringify({
      matricula,
      nome,
      codigo_perfil: codigoPerfil,
      id_empresa: vinculos?.id_empresa ?? null,
      id_turno: vinculos?.id_turno ?? null,
      id_local: vinculos?.id_local ?? null,
    }),
  });
}

export async function updateUserProfile(
  idUsuario: number,
  codigoPerfil: number,
  nome?: string,
  vinculos?: UsuarioVinculos,
) {
  return apiFetch<UserMutationResponse | ApiErrorBody>(`/users/${idUsuario}`, {
    method: 'PUT',
    body: JSON.stringify({
      codigo_perfil: codigoPerfil,
      ...(nome !== undefined ? { nome } : {}),
      id_empresa: vinculos?.id_empresa ?? null,
      id_turno: vinculos?.id_turno ?? null,
      id_local: vinculos?.id_local ?? null,
    }),
  });
}

export async function deleteUser(idUsuario: number) {
  return apiFetch<{ ok: boolean; mensagem?: string } | ApiErrorBody>(
    `/users/${idUsuario}`,
    { method: 'DELETE' },
  );
}

export async function resetUserPassword(idUsuario: number) {
  return apiFetch<UserMutationResponse | ApiErrorBody>(
    `/users/${idUsuario}/reset-password`,
    { method: 'POST' },
  );
}

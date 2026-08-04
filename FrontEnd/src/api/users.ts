import { apiFetch } from './client';
import type {
  ApiErrorBody,
  PerfisListResponse,
  UserMutationResponse,
  UsersListResponse,
} from '../types';

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

export async function createUser(
  matricula: string,
  nome: string,
  codigoPerfil: number,
) {
  return apiFetch<UserMutationResponse | ApiErrorBody>('/users', {
    method: 'POST',
    body: JSON.stringify({
      matricula,
      nome,
      codigo_perfil: codigoPerfil,
    }),
  });
}

export async function updateUserProfile(
  idUsuario: number,
  codigoPerfil: number,
  nome?: string,
) {
  return apiFetch<UserMutationResponse | ApiErrorBody>(`/users/${idUsuario}`, {
    method: 'PUT',
    body: JSON.stringify({
      codigo_perfil: codigoPerfil,
      ...(nome !== undefined ? { nome } : {}),
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

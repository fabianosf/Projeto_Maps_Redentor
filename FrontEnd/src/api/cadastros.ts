import { apiFetch } from './client';
import type { ApiErrorBody } from '../types';
import type { CadastrosMestres } from '../types/cadastros';

export async function getCadastros() {
  return apiFetch<
    { ok: true; cadastros: CadastrosMestres } | ApiErrorBody
  >('/cadastros', { method: 'GET' });
}

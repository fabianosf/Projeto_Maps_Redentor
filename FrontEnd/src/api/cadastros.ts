import { apiFetch } from './client';
import type { CadastrosResponse } from '@/types/cadastro';

export async function getCadastros(): Promise<CadastrosResponse> {
  return apiFetch<CadastrosResponse>('/cadastros', { method: 'GET' });
}

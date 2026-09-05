import { apiFetch } from './client';
import type { CadastrosResponse, VeiculoCadastro } from '@/types/cadastro';
import type { ApiSuccess } from '@/types/api';

export async function getCadastros(): Promise<CadastrosResponse> {
  return apiFetch<CadastrosResponse>('/cadastros', { method: 'GET' });
}

export type VeiculoCreateResponse = ApiSuccess<{ veiculo: VeiculoCadastro }>;

/** POST /cadastros/veiculos — placa no backend é só placeholder (= frota). */
export async function createVeiculo(payload: {
  numero_frota: string;
  id_empresa: number;
}): Promise<VeiculoCreateResponse> {
  return apiFetch<VeiculoCreateResponse>('/cadastros/veiculos', {
    method: 'POST',
    body: payload,
  });
}

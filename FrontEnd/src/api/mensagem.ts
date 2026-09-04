import { apiFetch } from './client';
import type { ApiSuccess } from '@/types/api';

export interface TipoAvaria {
  id_tip: number;
  descricao: string;
}

export type TiposAvariaResponse = ApiSuccess<{ tipos: TipoAvaria[] }>;

export type EnviarMensagemResponse = ApiSuccess<{
  mensagem?: string;
  avaria?: {
    id_av: number;
    id_vei: number;
    id_tip: number;
    id_usuario: number;
    data: string;
    texto?: string | null;
  };
}>;

export async function listTiposAvaria(): Promise<TiposAvariaResponse> {
  return apiFetch<TiposAvariaResponse>('/mensagem/tipos-avaria', {
    method: 'GET',
  });
}

export async function enviarMensagem(payload: {
  numero_frota: string;
  id_tip: number;
  texto: string;
}): Promise<EnviarMensagemResponse> {
  return apiFetch<EnviarMensagemResponse>('/mensagem', {
    method: 'POST',
    body: payload,
  });
}

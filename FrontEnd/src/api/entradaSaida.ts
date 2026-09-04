import { apiFetch } from './client';
import type { ApiErrorBody } from '../types';

export interface LinhaEntradaSaida {
  id_linha: number;
  codigo_linha?: number;
  descricao: string;
  id_local_origem?: number;
  id_local_destino?: number;
  codigo_origem?: number;
  descricao_origem?: string;
  codigo_destino?: number;
  descricao_destino?: string;
}

export interface LocalEntradaSaida {
  id_local: number;
  codigo_local?: number;
  descricao: string;
}

export interface EntradaSaidaContexto {
  ok: true;
  id_local_usuario: number | null;
  local_usuario: LocalEntradaSaida | null;
  linhas: LinhaEntradaSaida[];
  locais: LocalEntradaSaida[];
}

export async function getEntradaSaidaContexto() {
  return apiFetch<EntradaSaidaContexto | ApiErrorBody>('/entrada-saida/contexto', {
    method: 'GET',
  });
}

export async function getLinhasSaidaReferencia(idLinha: number) {
  return apiFetch<
    | { ok: true; linhas: LinhaEntradaSaida[] }
    | ApiErrorBody
  >(`/entrada-saida/linhas-saida?id_linha=${idLinha}`, { method: 'GET' });
}

export function formatLinhaLabel(l: LinhaEntradaSaida): string {
  const cod = l.codigo_linha != null ? String(l.codigo_linha) : String(l.id_linha);
  return `${cod}-${l.descricao ?? ''}`;
}

export function formatLocalLabel(l: LocalEntradaSaida): string {
  const cod = l.codigo_local != null ? String(l.codigo_local) : String(l.id_local);
  return `${cod} - ${l.descricao ?? ''}`;
}

export async function registrarEntradaSaida(body: {
  evento: 'C' | 'S';
  id_linha: number;
  carro: string;
  horario: string;
  temperatura?: string;
  roleta?: string;
  id_linha_destino?: number;
  id_destino?: number;
}) {
  return apiFetch<
    | { ok: true; mensagem?: string; evento?: string }
    | ApiErrorBody
  >('/entrada-saida/registrar', {
    method: 'POST',
    body: JSON.stringify(body),
  });
}

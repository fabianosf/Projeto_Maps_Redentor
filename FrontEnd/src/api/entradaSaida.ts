import { apiFetch } from './client';
import type {
  EntradaSaidaContextoResponse,
  EntradaSaidaRegistrarRequest,
  EntradaSaidaRegistrarResponse,
  LinhaEntradaSaida,
  LinhasSaidaResponse,
  LocalEntradaSaida,
} from '@/types/entradaSaida';

export type { LinhaEntradaSaida, LocalEntradaSaida };

export async function getEntradaSaidaContexto(): Promise<EntradaSaidaContextoResponse> {
  return apiFetch<EntradaSaidaContextoResponse>('/entrada-saida/contexto', {
    method: 'GET',
  });
}

export async function getLinhasSaidaReferencia(
  idLinha: number,
): Promise<LinhasSaidaResponse> {
  return apiFetch<LinhasSaidaResponse>(
    `/entrada-saida/linhas-saida?id_linha=${idLinha}`,
    { method: 'GET' },
  );
}

export function formatLinhaLabel(l: LinhaEntradaSaida): string {
  const cod = l.codigo_linha != null ? String(l.codigo_linha) : String(l.id_linha);
  return `${cod}-${l.descricao ?? ''}`;
}

export function formatLocalLabel(l: LocalEntradaSaida): string {
  const cod = l.codigo_local != null ? String(l.codigo_local) : String(l.id_local);
  return `${cod} - ${l.descricao ?? ''}`;
}

export async function registrarEntradaSaida(
  body: EntradaSaidaRegistrarRequest,
): Promise<EntradaSaidaRegistrarResponse> {
  return apiFetch<EntradaSaidaRegistrarResponse>('/entrada-saida/registrar', {
    method: 'POST',
    body,
  });
}

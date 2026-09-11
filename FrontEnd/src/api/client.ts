import type { ApiError } from '@/types/api';
import { isApiError } from '@/types/api';

const API_BASE_URL =
  import.meta.env.VITE_API_URL ??
  import.meta.env.VITE_API_BASE_URL ??
  '/api/v1';

/** Timeout padrão das chamadas HTTP (evita Promise pendente / UI congelada). */
export const API_DEFAULT_TIMEOUT_MS = 30_000;

export class SessionExpiredError extends Error {
  readonly status = 401 as const;

  constructor(message = 'Sessão expirada') {
    super(message);
    this.name = 'SessionExpiredError';
  }
}

export class ApiRequestError extends Error {
  readonly status: number;
  readonly body: ApiError;
  readonly details?: unknown;

  constructor(status: number, body: ApiError, details?: unknown) {
    super(body.mensagem);
    this.name = 'ApiRequestError';
    this.status = status;
    this.body = body;
    this.details = details;
  }
}

type SessionExpiredListener = () => void;

let sessionExpiredListener: SessionExpiredListener | null = null;

/** AuthContext registra o handler de sessão expirada (401). */
export function onSessionExpired(listener: SessionExpiredListener | null): void {
  sessionExpiredListener = listener;
}

function notifySessionExpired(): void {
  sessionExpiredListener?.();
}

function toApiError(data: unknown, fallback: string): ApiError {
  if (isApiError(data)) return data;
  if (data && typeof data === 'object') {
    const rec = data as Record<string, unknown>;
    const msg =
      (typeof rec.mensagem === 'string' && rec.mensagem) ||
      (typeof rec.message === 'string' && rec.message) ||
      (typeof rec.error === 'string' && rec.error) ||
      fallback;
    const codigo = typeof rec.codigo === 'string' ? rec.codigo : undefined;
    return { ok: false, mensagem: msg, codigo };
  }
  if (typeof data === 'string' && data.trim()) {
    return { ok: false, mensagem: data.trim().slice(0, 300) };
  }
  return { ok: false, mensagem: fallback };
}

export type ApiFetchOptions = Omit<RequestInit, 'body' | 'signal'> & {
  /** Corpo JSON (objeto ou já stringificado). */
  body?: BodyInit | object | null;
  /**
   * Se true, 401 não dispara “sessão expirada” (login / troca de senha).
   * Padrão: false.
   */
  skipSessionExpired?: boolean;
  /** Timeout em ms (padrão API_DEFAULT_TIMEOUT_MS). Use 0 para desabilitar. */
  timeoutMs?: number;
  signal?: AbortSignal;
};

function resolveBody(body: ApiFetchOptions['body']): BodyInit | undefined {
  if (body == null) return undefined;
  if (
    typeof body === 'string' ||
    body instanceof Blob ||
    body instanceof FormData ||
    body instanceof URLSearchParams ||
    body instanceof ArrayBuffer
  ) {
    return body;
  }
  return JSON.stringify(body);
}

function logDev(
  level: 'info' | 'error',
  method: string,
  url: string,
  extra?: Record<string, unknown>,
) {
  // Em DEV só registra falhas — sucesso não polui o console.
  if (!import.meta.env.DEV || level !== 'error') return;
  console.error('[API]', { method, url, ...extra });
}

/**
 * Fetch tipado com cookies de sessão (`credentials: 'include'`).
 * Em sucesso retorna o JSON como `T`. Em 401 (exceto skip) lança SessionExpiredError.
 * Sempre usa AbortController com timeout para não deixar Promise pendente.
 */
export async function apiFetch<T>(path: string, options: ApiFetchOptions = {}): Promise<T> {
  const {
    body,
    headers,
    skipSessionExpired = false,
    timeoutMs = API_DEFAULT_TIMEOUT_MS,
    signal: outerSignal,
    method = 'GET',
    ...rest
  } = options;
  const url = `${API_BASE_URL}${path.startsWith('/') ? path : `/${path}`}`;
  const resolvedBody = resolveBody(body);
  const httpMethod = String(method).toUpperCase();

  const controller = new AbortController();
  const onOuterAbort = () => controller.abort();
  if (outerSignal) {
    if (outerSignal.aborted) controller.abort();
    else outerSignal.addEventListener('abort', onOuterAbort, { once: true });
  }

  let timer: ReturnType<typeof setTimeout> | undefined;
  if (timeoutMs > 0) {
    timer = setTimeout(() => controller.abort(), timeoutMs);
  }

  logDev('info', httpMethod, url, {
    hasBody: resolvedBody != null,
    // não logar senha/token; payload só com chaves (dev)
    bodyKeys:
      resolvedBody && typeof body === 'object' && body != null && !(body instanceof FormData)
        ? Object.keys(body as object)
        : undefined,
  });

  try {
    const response = await fetch(url, {
      ...rest,
      method: httpMethod,
      credentials: 'include',
      signal: controller.signal,
      headers: {
        Accept: 'application/json',
        ...(resolvedBody != null && !(resolvedBody instanceof FormData)
          ? { 'Content-Type': 'application/json' }
          : {}),
        ...(headers ?? {}),
      },
      body: resolvedBody,
    });

    const rawText = await response.text();
    let data: unknown = {};
    if (rawText.trim()) {
      try {
        data = JSON.parse(rawText) as unknown;
      } catch {
        data = {
          ok: false,
          mensagem: `Resposta inválida da API (HTTP ${response.status}).`,
          codigo: 'resposta_invalida',
        };
      }
    }

    if (response.status === 401 && !skipSessionExpired) {
      notifySessionExpired();
      throw new SessionExpiredError(toApiError(data, 'Sessão expirada').mensagem);
    }

    if (!response.ok) {
      const fallback =
        response.status === 404
          ? 'Recurso não encontrado.'
          : response.status === 405
            ? 'Consulta não disponível neste endereço (método não permitido). Reinicie a API ou tente novamente.'
            : response.status >= 500
              ? 'Não foi possível concluir a operação. Tente novamente.'
              : `Erro HTTP ${response.status}`;
      const errBody = toApiError(
        rawText.trim()
          ? data
          : {
              ok: false,
              mensagem: fallback,
              codigo:
                response.status === 404
                  ? 'nao_encontrado'
                  : response.status === 405
                    ? 'metodo_nao_permitido'
                    : 'http_error',
            },
        fallback,
      );
      if (!errBody.codigo && response.status === 404) {
        errBody.codigo = 'nao_encontrado';
      }
      if (!errBody.codigo && response.status === 405) {
        errBody.codigo = 'metodo_nao_permitido';
      }
      // Flask 405 costuma devolver HTML/texto genérico — preferir mensagem amigável.
      if (response.status === 405) {
        const generica =
          !rawText.trim() ||
          errBody.codigo === 'resposta_invalida' ||
          /method not allowed|not allowed|resposta inválida|erro http/i.test(
            errBody.mensagem,
          );
        if (generica) {
          errBody.mensagem = fallback;
          errBody.codigo = 'metodo_nao_permitido';
        }
      }
      logDev('error', httpMethod, url, {
        status: response.status,
        codigo: errBody.codigo,
        mensagem: errBody.mensagem,
      });
      throw new ApiRequestError(response.status, errBody, data);
    }

    return data as T;
  } catch (err) {
    if (err instanceof SessionExpiredError || err instanceof ApiRequestError) {
      throw err;
    }
    const aborted =
      (err instanceof DOMException && err.name === 'AbortError') ||
      (err instanceof Error && err.name === 'AbortError');
    if (aborted) {
      const body: ApiError = {
        ok: false,
        mensagem: 'Tempo esgotado na comunicação com a API. Tente novamente.',
        codigo: 'timeout',
      };
      logDev('error', httpMethod, url, { status: 0, codigo: 'timeout' });
      throw new ApiRequestError(0, body);
    }
    const body: ApiError = {
      ok: false,
      mensagem: 'Falha de rede. Verifique a conexão e tente novamente.',
      codigo: 'rede',
    };
    logDev('error', httpMethod, url, {
      status: 0,
      codigo: 'rede',
      detail: err instanceof Error ? err.message : String(err),
    });
    throw new ApiRequestError(0, body, err);
  } finally {
    if (timer != null) clearTimeout(timer);
    if (outerSignal) outerSignal.removeEventListener('abort', onOuterAbort);
  }
}

export function getApiBaseUrl(): string {
  return API_BASE_URL;
}

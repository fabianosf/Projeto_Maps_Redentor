import type { ApiError } from '@/types/api';
import { isApiError } from '@/types/api';

const API_BASE_URL =
  import.meta.env.VITE_API_URL ??
  import.meta.env.VITE_API_BASE_URL ??
  '/api/v1';

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

  constructor(status: number, body: ApiError) {
    super(body.mensagem);
    this.name = 'ApiRequestError';
    this.status = status;
    this.body = body;
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
  return { ok: false, mensagem: fallback };
}

export type ApiFetchOptions = Omit<RequestInit, 'body'> & {
  /** Corpo JSON (objeto ou já stringificado). */
  body?: BodyInit | object | null;
  /**
   * Se true, 401 não dispara “sessão expirada” (login / troca de senha).
   * Padrão: false.
   */
  skipSessionExpired?: boolean;
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

/**
 * Fetch tipado com cookies de sessão (`credentials: 'include'`).
 * Em sucesso retorna o JSON como `T`. Em 401 (exceto skip) lança SessionExpiredError.
 */
export async function apiFetch<T>(path: string, options: ApiFetchOptions = {}): Promise<T> {
  const { body, headers, skipSessionExpired = false, ...rest } = options;
  const url = `${API_BASE_URL}${path.startsWith('/') ? path : `/${path}`}`;
  const resolvedBody = resolveBody(body);

  const response = await fetch(url, {
    ...rest,
    credentials: 'include',
    headers: {
      Accept: 'application/json',
      ...(resolvedBody != null && !(resolvedBody instanceof FormData)
        ? { 'Content-Type': 'application/json' }
        : {}),
      ...(headers ?? {}),
    },
    body: resolvedBody,
  });

  const data: unknown = await response.json().catch(() => ({}));

  if (response.status === 401 && !skipSessionExpired) {
    notifySessionExpired();
    throw new SessionExpiredError(toApiError(data, 'Sessão expirada').mensagem);
  }

  if (!response.ok) {
    throw new ApiRequestError(response.status, toApiError(data, `Erro HTTP ${response.status}`));
  }

  return data as T;
}

export function getApiBaseUrl(): string {
  return API_BASE_URL;
}

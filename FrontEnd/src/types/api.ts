/** Envelopes genéricos da API RedMapa — sem `any`. */

export type ApiSuccess<T extends object = Record<string, never>> = { ok: true } & T;

export interface ApiError {
  ok: false;
  mensagem: string;
  codigo?: string;
  /** ID de correlação da API (suporte / logs). */
  correlation_id?: string;
}

export type ApiResult<T extends object> = ApiSuccess<T> | ApiError;

export function isApiError(value: unknown): value is ApiError {
  if (typeof value !== 'object' || value === null) return false;
  const v = value as Record<string, unknown>;
  return v.ok === false && typeof v.mensagem === 'string';
}

export function isApiSuccess<T extends object>(value: unknown): value is ApiSuccess<T> {
  if (typeof value !== 'object' || value === null) return false;
  return (value as Record<string, unknown>).ok === true;
}

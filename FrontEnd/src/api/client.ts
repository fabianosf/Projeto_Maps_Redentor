const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? '/api/v1';

export async function apiFetch<T = unknown>(
  path: string,
  options: RequestInit = {},
): Promise<{ response: Response; data: T }> {
  const url = `${API_BASE_URL}${path.startsWith('/') ? path : `/${path}`}`;

  const response = await fetch(url, {
    ...options,
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'application/json',
      ...(options.headers ?? {}),
    },
  });

  const data = (await response.json().catch(() => ({}))) as T;
  return { response, data };
}

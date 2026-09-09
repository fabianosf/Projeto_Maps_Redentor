import { afterEach, describe, expect, it, vi } from 'vitest';
import { apiFetch, ApiRequestError } from '@/api/client';

describe('apiFetch', () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it('lança ApiRequestError com timeout quando AbortError', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn((_url: string, init?: RequestInit) => {
        return new Promise((_resolve, reject) => {
          init?.signal?.addEventListener('abort', () => {
            reject(new DOMException('Aborted', 'AbortError'));
          });
        });
      }),
    );

    await expect(
      apiFetch('/mapas/ocupacao', { method: 'GET', timeoutMs: 20 }),
    ).rejects.toMatchObject({
      name: 'ApiRequestError',
      status: 0,
      message: expect.stringMatching(/tempo esgotado/i),
    });
  });

  it('trata resposta não-JSON sem travar', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async () =>
        new Response('not-json', {
          status: 500,
          headers: { 'Content-Type': 'text/plain' },
        }),
      ),
    );

    try {
      await apiFetch('/mapas/1', { method: 'GET', timeoutMs: 5000 });
      expect.fail('deveria lançar');
    } catch (err) {
      expect(err).toBeInstanceOf(ApiRequestError);
      expect((err as ApiRequestError).status).toBe(500);
      expect((err as ApiRequestError).message.length).toBeGreaterThan(0);
    }
  });
});

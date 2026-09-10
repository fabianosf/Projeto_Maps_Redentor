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

  it('404 com corpo vazio vira ApiRequestError seguro', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async () =>
        new Response('', {
          status: 404,
          statusText: 'Not Found',
          headers: { 'Content-Type': 'application/json' },
        }),
      ),
    );

    try {
      await apiFetch('/mapas/99999', { method: 'GET', timeoutMs: 5000 });
      expect.fail('deveria lançar');
    } catch (err) {
      expect(err).toBeInstanceOf(ApiRequestError);
      const e = err as ApiRequestError;
      expect(e.status).toBe(404);
      expect(e.body.codigo).toBe('nao_encontrado');
      expect(e.message).toMatch(/não encontrado/i);
    }
  });

  it('404 com JSON de negócio preserva mensagem da API', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async () =>
        new Response(
          JSON.stringify({
            ok: false,
            mensagem: 'MAPA não encontrado.',
            codigo: 'nao_encontrado',
          }),
          {
            status: 404,
            headers: { 'Content-Type': 'application/json' },
          },
        ),
      ),
    );

    await expect(apiFetch('/mapas/4', { method: 'GET' })).rejects.toMatchObject({
      status: 404,
      message: 'MAPA não encontrado.',
      body: { codigo: 'nao_encontrado' },
    });
  });

  it('405 com corpo vazio/HTML vira mensagem amigável', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async () =>
        new Response('<!doctype html><title>405 Method Not Allowed</title>', {
          status: 405,
          statusText: 'Method Not Allowed',
          headers: { 'Content-Type': 'text/html' },
        }),
      ),
    );

    try {
      await apiFetch('/guia?data=10%2F09%2F2026', { method: 'GET', timeoutMs: 5000 });
      expect.fail('deveria lançar');
    } catch (err) {
      expect(err).toBeInstanceOf(ApiRequestError);
      const e = err as ApiRequestError;
      expect(e.status).toBe(405);
      expect(e.body.codigo).toBe('metodo_nao_permitido');
      expect(e.message).toMatch(/método não permitido|consulta não disponível/i);
    }
  });
});

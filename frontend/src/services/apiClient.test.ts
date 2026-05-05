import { afterEach, describe, expect, it, vi } from 'vitest';

import { apiGet, apiPost } from './apiClient';

describe('apiClient', () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('returns JSON for successful GET requests', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(JSON.stringify({ status: 'ok' }), { status: 200 }),
    );

    await expect(apiGet('/health')).resolves.toEqual({ status: 'ok' });
  });

  it('sends JSON bodies for POST requests', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(JSON.stringify({ created: true }), { status: 200 }),
    );

    await apiPost('/items', { name: 'Fries' });

    expect(fetchMock).toHaveBeenCalledWith(
      'http://localhost:8000/items',
      expect.objectContaining({
        body: JSON.stringify({ name: 'Fries' }),
        headers: { 'Content-Type': 'application/json' },
        method: 'POST',
      }),
    );
  });

  it('throws ApiError for failed responses', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response(null, { status: 500 }));

    await expect(apiGet('/broken')).rejects.toMatchObject({
      message: 'Request failed with status 500',
      status: 500,
    });
  });
});

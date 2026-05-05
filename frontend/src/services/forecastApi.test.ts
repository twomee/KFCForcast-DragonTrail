import { afterEach, describe, expect, it, vi } from 'vitest';

import { generateForecasts, getForecasts, getStores } from './forecastApi';

describe('forecastApi', () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('calls the stores endpoint', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(JSON.stringify([{ id: 1, name: 'Dizengoff Center' }]), { status: 200 }),
    );

    await getStores();

    expect(fetchMock).toHaveBeenCalledWith('http://localhost:8000/api/v1/stores');
  });

  it('calls the forecasts endpoint with store and date query params', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(JSON.stringify([]), { status: 200 }),
    );

    await getForecasts(7, '2026-05-06');

    expect(fetchMock).toHaveBeenCalledWith(
      'http://localhost:8000/api/v1/forecasts?store_id=7&date=2026-05-06',
    );
  });

  it('posts forecast generation payloads', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(JSON.stringify({ forecast_date: '2026-05-06', rows_generated: 24 }), {
        status: 200,
      }),
    );

    await generateForecasts('2026-05-06');

    expect(fetchMock).toHaveBeenCalledWith(
      'http://localhost:8000/api/v1/forecasts/generate',
      expect.objectContaining({
        body: JSON.stringify({ forecast_date: '2026-05-06' }),
        method: 'POST',
      }),
    );
  });
});

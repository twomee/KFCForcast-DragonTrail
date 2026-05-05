import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { ForecastDashboard } from './ForecastDashboard';

function renderPage() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <ForecastDashboard />
    </QueryClientProvider>,
  );
}

describe('ForecastDashboard', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('loads stores and renders forecast rows', async () => {
    vi.spyOn(globalThis, 'fetch').mockImplementation((input) => {
      const url = String(input);
      if (url.includes('/stores')) {
        return Promise.resolve(
          new Response(JSON.stringify([{ id: 1, name: 'Dizengoff Center' }]), { status: 200 }),
        );
      }

      return Promise.resolve(
        new Response(
          JSON.stringify([
            {
              id: 1,
              store_id: 1,
              store_name: 'Dizengoff Center',
              product_id: 1,
              product_name: 'Fries',
              forecast_date: '2026-05-05',
              hour: 12,
              predicted_quantity: 41,
            },
          ]),
          { status: 200 },
        ),
      );
    });

    renderPage();

    expect(await screen.findByRole('heading', { name: 'Dizengoff Center' })).toBeInTheDocument();
    await waitFor(() => expect(screen.getByText('Fries')).toBeInTheDocument());
    expect(screen.getByRole('button', { name: /12:00 41 units/i })).toBeInTheDocument();
  });

  it('triggers forecast generation for the selected date', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockImplementation((input, init) => {
      const url = String(input);
      if (url.includes('/stores')) {
        return Promise.resolve(
          new Response(JSON.stringify([{ id: 1, name: 'Dizengoff Center' }]), { status: 200 }),
        );
      }

      if (url.includes('/forecasts/generate') && init?.method === 'POST') {
        return Promise.resolve(
          new Response(JSON.stringify({ forecast_date: '2026-05-05', rows_generated: 24 }), {
            status: 200,
          }),
        );
      }

      return Promise.resolve(new Response(JSON.stringify([]), { status: 200 }));
    });

    renderPage();

    await screen.findByRole('heading', { name: 'Dizengoff Center' });
    await userEvent.click(screen.getByRole('button', { name: /generate/i }));

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith(
        expect.stringContaining('/api/v1/forecasts/generate'),
        expect.objectContaining({
          body: expect.stringContaining('forecast_date'),
          method: 'POST',
        }),
      );
    });
  });
});

import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it } from 'vitest';

import { ForecastTable } from './ForecastTable';

describe('ForecastTable', () => {
  it('renders an empty state when there are no forecasts', () => {
    render(<ForecastTable forecasts={[]} />);

    expect(screen.getByRole('heading', { name: 'No forecasts found' })).toBeInTheDocument();
  });

  it('groups forecasts by hour and opens the first hour by default', () => {
    render(
      <ForecastTable
        forecasts={[
          {
            id: 1,
            store_id: 1,
            store_name: 'Dizengoff Center',
            product_id: 3,
            product_name: 'Fries',
            forecast_date: '2026-05-06',
            hour: 8,
            predicted_quantity: 17,
          },
          {
            id: 2,
            store_id: 1,
            store_name: 'Dizengoff Center',
            product_id: 2,
            product_name: 'Burger',
            forecast_date: '2026-05-06',
            hour: 8,
            predicted_quantity: 23,
          },
          {
            id: 3,
            store_id: 1,
            store_name: 'Dizengoff Center',
            product_id: 4,
            product_name: 'Wings',
            forecast_date: '2026-05-06',
            hour: 12,
            predicted_quantity: 31,
          },
        ]}
      />,
    );

    expect(screen.getByRole('button', { name: /08:00 40 units/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /12:00 31 units/i })).toBeInTheDocument();
    expect(screen.getByText('Fries')).toBeInTheDocument();
    expect(screen.getByText('17')).toBeInTheDocument();
    expect(screen.queryByText('Wings')).not.toBeInTheDocument();
  });

  it('shows products for the selected hour', async () => {
    render(
      <ForecastTable
        forecasts={[
          {
            id: 1,
            store_id: 1,
            store_name: 'Dizengoff Center',
            product_id: 3,
            product_name: 'Fries',
            forecast_date: '2026-05-06',
            hour: 8,
            predicted_quantity: 17,
          },
          {
            id: 2,
            store_id: 1,
            store_name: 'Dizengoff Center',
            product_id: 4,
            product_name: 'Wings',
            forecast_date: '2026-05-06',
            hour: 12,
            predicted_quantity: 31,
          },
        ]}
      />,
    );

    await userEvent.click(screen.getByRole('button', { name: /12:00 31 units/i }));

    expect(screen.getByRole('heading', { name: '12:00' })).toBeInTheDocument();
    expect(screen.getByText('Wings')).toBeInTheDocument();
    expect(screen.queryByText('Fries')).not.toBeInTheDocument();
  });
});

import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { ForecastTable } from './ForecastTable';

describe('ForecastTable', () => {
  it('renders an empty state when there are no forecasts', () => {
    render(<ForecastTable forecasts={[]} />);

    expect(screen.getByRole('heading', { name: 'No forecasts found' })).toBeInTheDocument();
  });

  it('renders forecast rows with padded hour labels', () => {
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
        ]}
      />,
    );

    expect(screen.getByText('08:00')).toBeInTheDocument();
    expect(screen.getByText('Fries')).toBeInTheDocument();
    expect(screen.getByText('17')).toBeInTheDocument();
  });
});

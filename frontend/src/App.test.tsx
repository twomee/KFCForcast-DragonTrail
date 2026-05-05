import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { App } from './App';

vi.mock('./pages/ForecastDashboard', () => ({
  ForecastDashboard: () => <main>Forecast dashboard</main>,
}));

describe('App', () => {
  it('renders the forecast dashboard inside the query provider', () => {
    render(<App />);

    expect(screen.getByText('Forecast dashboard')).toBeInTheDocument();
  });
});

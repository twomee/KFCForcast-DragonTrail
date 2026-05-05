import type { Forecast } from '../types/api';

type ForecastTableProps = {
  forecasts: Forecast[];
};

export function ForecastTable({ forecasts }: ForecastTableProps) {
  if (forecasts.length === 0) {
    return (
      <section className="empty-state">
        <h2>No forecasts found</h2>
        <p>Generate forecasts for the selected date or choose another store/date.</p>
      </section>
    );
  }

  return (
    <section className="table-shell" aria-label="Forecast results">
      <table>
        <thead>
          <tr>
            <th>Hour</th>
            <th>Product</th>
            <th>Predicted units</th>
          </tr>
        </thead>
        <tbody>
          {forecasts.map((forecast) => (
            <tr key={forecast.id}>
              <td>{String(forecast.hour).padStart(2, '0')}:00</td>
              <td>{forecast.product_name}</td>
              <td>{forecast.predicted_quantity}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}


import { useMemo, useState } from 'react';

import type { Forecast } from '../types/api';

type ForecastTableProps = {
  forecasts: Forecast[];
};

type HourForecastGroup = {
  hour: number;
  totalQuantity: number;
  forecasts: Forecast[];
};

function formatHour(hour: number): string {
  return `${String(hour).padStart(2, '0')}:00`;
}

function groupForecastsByHour(forecasts: Forecast[]): HourForecastGroup[] {
  const groups = new Map<number, Forecast[]>();

  for (const forecast of forecasts) {
    const hourForecasts = groups.get(forecast.hour) ?? [];
    hourForecasts.push(forecast);
    groups.set(forecast.hour, hourForecasts);
  }

  return Array.from(groups.entries())
    .sort(([leftHour], [rightHour]) => leftHour - rightHour)
    .map(([hour, hourForecasts]) => {
      const sortedForecasts = [...hourForecasts].sort((left, right) =>
        left.product_name.localeCompare(right.product_name),
      );

      return {
        hour,
        forecasts: sortedForecasts,
        totalQuantity: sortedForecasts.reduce(
          (total, forecast) => total + forecast.predicted_quantity,
          0,
        ),
      };
    });
}

export function ForecastTable({ forecasts }: ForecastTableProps) {
  const hourlyForecasts = useMemo(() => groupForecastsByHour(forecasts), [forecasts]);
  const [selectedHour, setSelectedHour] = useState<number | null>(null);
  const selectedHourForecast =
    hourlyForecasts.find((group) => group.hour === selectedHour) ?? hourlyForecasts[0];
  const effectiveSelectedHour = selectedHourForecast?.hour ?? null;

  if (forecasts.length === 0) {
    return (
      <section className="empty-state">
        <h2>No forecasts found</h2>
        <p>Generate forecasts for the selected date or choose another store/date.</p>
      </section>
    );
  }

  return (
    <section className="forecast-explorer" aria-label="Forecast results">
      <div className="hour-strip" aria-label="Forecast hours">
        {hourlyForecasts.map((group) => {
          const isSelected = group.hour === effectiveSelectedHour;

          return (
            <button
              aria-label={`${formatHour(group.hour)} ${group.totalQuantity} units`}
              aria-pressed={isSelected}
              className="hour-button"
              key={group.hour}
              onClick={() => setSelectedHour(group.hour)}
              type="button"
            >
              <span className="hour-button__time">{formatHour(group.hour)}</span>
              <span className="hour-button__total">{group.totalQuantity} units</span>
            </button>
          );
        })}
      </div>

      {selectedHourForecast && (
        <div className="hour-detail">
          <div className="hour-detail__header">
            <div>
              <p className="eyebrow">Selected hour</p>
              <h2>{formatHour(selectedHourForecast.hour)}</h2>
            </div>
            <div className="hour-total">
              <span>{selectedHourForecast.totalQuantity}</span>
              <small>total units</small>
            </div>
          </div>

          <div
            aria-label={`${formatHour(selectedHourForecast.hour)} products`}
            className="product-grid"
          >
            {selectedHourForecast.forecasts.map((forecast) => (
              <div className="product-row" key={forecast.id}>
                <span>{forecast.product_name}</span>
                <strong>{forecast.predicted_quantity}</strong>
              </div>
            ))}
          </div>
        </div>
      )}
    </section>
  );
}

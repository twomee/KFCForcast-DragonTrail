import { useMemo, useState } from 'react';

import { ForecastControls } from '../components/ForecastControls';
import { ForecastTable } from '../components/ForecastTable';
import { useForecasts, useGenerateForecasts } from '../hooks/useForecasts';
import { useStores } from '../hooks/useStores';

function tomorrowIsoDate(): string {
  const tomorrow = new Date();
  tomorrow.setDate(tomorrow.getDate() + 1);
  const year = tomorrow.getFullYear();
  const month = String(tomorrow.getMonth() + 1).padStart(2, '0');
  const day = String(tomorrow.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

export function ForecastDashboard() {
  const [selectedStoreId, setSelectedStoreId] = useState<number | null>(null);
  const [selectedDate, setSelectedDate] = useState(tomorrowIsoDate());
  const storesQuery = useStores();
  const effectiveStoreId = selectedStoreId ?? storesQuery.data?.[0]?.id ?? null;
  const canGenerateForecasts = effectiveStoreId !== null && selectedDate.length > 0;
  const forecastsQuery = useForecasts(effectiveStoreId, selectedDate);
  const generateMutation = useGenerateForecasts(effectiveStoreId, selectedDate);

  const selectedStoreName = useMemo(() => {
    return storesQuery.data?.find((store) => store.id === effectiveStoreId)?.name ?? 'Selected store';
  }, [effectiveStoreId, storesQuery.data]);

  if (storesQuery.isLoading) {
    return <main className="page-state">Loading stores...</main>;
  }

  if (storesQuery.isError) {
    return <main className="page-state">Unable to load stores.</main>;
  }

  return (
    <main className="app-shell">
      <header className="page-header">
        <div>
          <p className="eyebrow">KFC Forecast</p>
          <h1>{selectedStoreName}</h1>
        </div>
        <p className="summary">Hourly product demand forecast for kitchen preparation.</p>
      </header>

      <ForecastControls
        stores={storesQuery.data ?? []}
        selectedStoreId={effectiveStoreId}
        selectedDate={selectedDate}
        isGenerating={generateMutation.isPending}
        canGenerate={canGenerateForecasts}
        onStoreChange={setSelectedStoreId}
        onDateChange={setSelectedDate}
        onGenerate={() => generateMutation.mutate()}
      />

      {generateMutation.isError && (
        <div className="inline-alert" role="alert">
          Forecast generation failed.
        </div>
      )}

      {forecastsQuery.isLoading && <section className="page-state">Loading forecasts...</section>}
      {forecastsQuery.isError && (
        <section className="page-state">Unable to load forecasts for this selection.</section>
      )}
      {forecastsQuery.data && (
        <ForecastTable
          key={`${effectiveStoreId ?? 'no-store'}-${selectedDate}`}
          forecasts={forecastsQuery.data}
        />
      )}
    </main>
  );
}

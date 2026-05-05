import { CalendarDays, RefreshCw, Store as StoreIcon } from 'lucide-react';

import type { Store } from '../types/api';

type ForecastControlsProps = {
  stores: Store[];
  selectedStoreId: number | null;
  selectedDate: string;
  isGenerating: boolean;
  canGenerate: boolean;
  onStoreChange: (storeId: number) => void;
  onDateChange: (date: string) => void;
  onGenerate: () => void;
};

export function ForecastControls({
  stores,
  selectedStoreId,
  selectedDate,
  isGenerating,
  canGenerate,
  onStoreChange,
  onDateChange,
  onGenerate,
}: ForecastControlsProps) {
  return (
    <section className="controls" aria-label="Forecast filters">
      <label className="field">
        <span>
          <StoreIcon size={16} aria-hidden="true" />
          Store
        </span>
        <select
          value={selectedStoreId ?? ''}
          onChange={(event) => onStoreChange(Number(event.target.value))}
        >
          {stores.map((store) => (
            <option key={store.id} value={store.id}>
              {store.name}
            </option>
          ))}
        </select>
      </label>

      <label className="field">
        <span>
          <CalendarDays size={16} aria-hidden="true" />
          Forecast date
        </span>
        <input
          type="date"
          value={selectedDate}
          onChange={(event) => onDateChange(event.target.value)}
        />
      </label>

      <button
        className="generate-button"
        type="button"
        onClick={onGenerate}
        disabled={isGenerating || !canGenerate}
      >
        <RefreshCw size={16} aria-hidden="true" />
        {isGenerating ? 'Generating' : 'Generate'}
      </button>
    </section>
  );
}

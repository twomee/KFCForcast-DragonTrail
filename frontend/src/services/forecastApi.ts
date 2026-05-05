import { apiGet, apiPost } from './apiClient';
import type { Forecast, ForecastGenerateResponse, Store } from '../types/api';

export function getStores(): Promise<Store[]> {
  return apiGet<Store[]>('/api/v1/stores');
}

export function getForecasts(storeId: number, forecastDate: string): Promise<Forecast[]> {
  const params = new URLSearchParams({
    store_id: String(storeId),
    date: forecastDate,
  });
  return apiGet<Forecast[]>(`/api/v1/forecasts?${params.toString()}`);
}

export function generateForecasts(forecastDate: string): Promise<ForecastGenerateResponse> {
  return apiPost<ForecastGenerateResponse>('/api/v1/forecasts/generate', {
    forecast_date: forecastDate,
  });
}


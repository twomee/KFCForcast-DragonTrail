export type Store = {
  id: number;
  name: string;
};

export type Forecast = {
  id: number;
  store_id: number;
  store_name: string;
  product_id: number;
  product_name: string;
  forecast_date: string;
  hour: number;
  predicted_quantity: number;
};

export type ForecastGenerateResponse = {
  forecast_date: string;
  rows_generated: number;
};


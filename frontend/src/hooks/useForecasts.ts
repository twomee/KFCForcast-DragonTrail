import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { generateForecasts, getForecasts } from '../services/forecastApi';

export function useForecasts(storeId: number | null, forecastDate: string) {
  return useQuery({
    queryKey: ['forecasts', storeId, forecastDate],
    queryFn: () => getForecasts(storeId as number, forecastDate),
    enabled: storeId !== null && forecastDate.length > 0,
  });
}

export function useGenerateForecasts(storeId: number | null, forecastDate: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () => generateForecasts(forecastDate),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['forecasts', storeId, forecastDate] });
    },
  });
}


import { useQuery } from '@tanstack/react-query';

import { getStores } from '../services/forecastApi';

export function useStores() {
  return useQuery({
    queryKey: ['stores'],
    queryFn: getStores,
  });
}


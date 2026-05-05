import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

import { ForecastDashboard } from './pages/ForecastDashboard';

const queryClient = new QueryClient();

export function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ForecastDashboard />
    </QueryClientProvider>
  );
}


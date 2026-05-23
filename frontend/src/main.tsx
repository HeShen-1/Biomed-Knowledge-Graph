import React from 'react';
import ReactDOM from 'react-dom/client';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import App from './App';
import './styles/ibm-carbon.css';

// Initialize theme from localStorage
let saved: string;
try {
  saved = localStorage.getItem('biomed-theme') || 'dark';
} catch {
  saved = 'dark';
}
document.documentElement.setAttribute('data-theme', saved);

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { staleTime: 60_000, retry: 1 },
  },
});

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <App />
    </QueryClientProvider>
  </React.StrictMode>,
);

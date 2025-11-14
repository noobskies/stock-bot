import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ReactQueryDevtools } from "@tanstack/react-query-devtools";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { Toaster } from "@/components/ui/sonner";

import { AppLayout } from "@/components/layout/AppLayout";
import { DashboardPage } from "@/pages/DashboardPage";
import { TradesPage } from "@/pages/TradesPage";
import { SignalsPage } from "@/pages/SignalsPage";
import { SettingsPage } from "@/pages/SettingsPage";

// Create a client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30000, // 30 seconds
      refetchOnWindowFocus: false,
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route element={<AppLayout />}>
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/trades" element={<TradesPage />} />
            <Route path="/signals" element={<SignalsPage />} />
            <Route path="/settings" element={<SettingsPage />} />
          </Route>
        </Routes>
        <Toaster position="top-right" richColors closeButton />
      </BrowserRouter>
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  );
}

export default App;

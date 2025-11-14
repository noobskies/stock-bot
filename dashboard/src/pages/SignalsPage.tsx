import { useQuery } from "@tanstack/react-query";
import { getSignalHistory } from "@/lib/api/signals";
import { SignalsTable } from "@/components/dashboard/SignalsTable";
import { SignalStats } from "@/components/dashboard/SignalStats";
import { LoadingSpinner } from "@/components/shared/LoadingSpinner";
import { ErrorMessage } from "@/components/shared/ErrorMessage";
import type { TradingSignal } from "@/types";

export function SignalsPage() {
  const {
    data: signals,
    isLoading,
    error,
    refetch,
  } = useQuery<TradingSignal[], Error>({
    queryKey: ["signals", "history", 30],
    queryFn: () => getSignalHistory(30),
    staleTime: 60000,
    retry: 3,
  });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Signal History</h1>
        <p className="text-muted-foreground">
          View ML predictions and signal generation history (last 30 days)
        </p>
      </div>

      {error ? (
        <ErrorMessage
          error={error}
          title="Failed to load signals"
          retry={refetch}
        />
      ) : (
        <>
          <SignalStats signals={signals || []} />

          {isLoading ? (
            <div className="flex items-center justify-center p-12">
              <LoadingSpinner size="lg" text="Loading signals..." />
            </div>
          ) : (
            <SignalsTable signals={signals || []} isLoading={isLoading} />
          )}
        </>
      )}
    </div>
  );
}

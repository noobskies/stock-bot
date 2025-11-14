import { useState, useCallback } from "react";
import { useTrades } from "@/lib/hooks/useTrades";
import { TradesTable } from "@/components/dashboard/TradesTable";
import { TradeFilters } from "@/components/dashboard/TradeFilters";
import { TradeStats } from "@/components/dashboard/TradeStats";
import { LoadingSpinner } from "@/components/shared/LoadingSpinner";
import { ErrorMessage } from "@/components/shared/ErrorMessage";
import type { TradeFilters as TradeFiltersType } from "@/types";

export function TradesPage() {
  const [filters, setFilters] = useState<TradeFiltersType>({});
  const { data: trades, isLoading, error, refetch } = useTrades(filters);

  const handleFilterChange = useCallback((newFilters: TradeFiltersType) => {
    setFilters(newFilters);
  }, []);

  const handleReset = useCallback(() => {
    setFilters({});
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Trade History</h1>
        <p className="text-muted-foreground">
          View and analyze your complete trading history
        </p>
      </div>

      {error ? (
        <ErrorMessage
          error={error}
          title="Failed to load trades"
          retry={refetch}
        />
      ) : (
        <>
          <TradeStats trades={trades || []} />

          <TradeFilters
            filters={filters}
            onFilterChange={handleFilterChange}
            onReset={handleReset}
          />

          {isLoading ? (
            <div className="flex items-center justify-center p-12">
              <LoadingSpinner size="lg" text="Loading trades..." />
            </div>
          ) : (
            <TradesTable trades={trades || []} isLoading={isLoading} />
          )}
        </>
      )}
    </div>
  );
}

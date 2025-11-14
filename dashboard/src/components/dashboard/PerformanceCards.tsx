import { TrendingUp, Target, Activity, BarChart3 } from "lucide-react";
import { usePortfolio } from "@/lib/hooks/usePortfolio";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { LoadingSpinner } from "@/components/shared/LoadingSpinner";
import { ErrorMessage } from "@/components/shared/ErrorMessage";
import { formatPercent, formatNumber } from "@/lib/utils/format";

export function PerformanceCards() {
  const { data: portfolio, isLoading, error, refetch } = usePortfolio();

  if (isLoading) {
    return (
      <div className="grid gap-4 md:grid-cols-2">
        {[...Array(4)].map((_, i) => (
          <Card key={i}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Loading...</CardTitle>
            </CardHeader>
            <CardContent>
              <LoadingSpinner size="sm" />
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Performance Metrics</CardTitle>
        </CardHeader>
        <CardContent>
          <ErrorMessage error={error} retry={refetch} />
        </CardContent>
      </Card>
    );
  }

  const performance = portfolio?.performance;
  const winRate = performance?.win_rate ?? 0;
  const totalTrades = performance?.total_trades ?? 0;
  const sharpeRatio = performance?.sharpe_ratio ?? 0;
  const maxDrawdown = performance?.max_drawdown ?? 0;

  // Helper to determine color based on value
  const getWinRateColor = (rate: number) => {
    if (rate >= 0.6) return "text-green-500";
    if (rate >= 0.5) return "text-yellow-500";
    return "text-red-500";
  };

  const getSharpeColor = (ratio: number) => {
    if (ratio >= 1.5) return "text-green-500";
    if (ratio >= 1.0) return "text-yellow-500";
    return "text-red-500";
  };

  const getDrawdownColor = (drawdown: number) => {
    const absDrawdown = Math.abs(drawdown);
    if (absDrawdown <= 0.05) return "text-green-500";
    if (absDrawdown <= 0.1) return "text-yellow-500";
    return "text-red-500";
  };

  return (
    <div className="grid gap-4 md:grid-cols-2">
      {/* Win Rate */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Win Rate</CardTitle>
          <Target className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className={`text-2xl font-bold ${getWinRateColor(winRate)}`}>
            {formatPercent(winRate, 1)}
          </div>
          <p className="text-xs text-muted-foreground">Profitable trades</p>
        </CardContent>
      </Card>

      {/* Total Trades */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Total Trades</CardTitle>
          <BarChart3 className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">
            {formatNumber(totalTrades, 0)}
          </div>
          <p className="text-xs text-muted-foreground">Executed trades</p>
        </CardContent>
      </Card>

      {/* Sharpe Ratio */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Sharpe Ratio</CardTitle>
          <TrendingUp className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className={`text-2xl font-bold ${getSharpeColor(sharpeRatio)}`}>
            {formatNumber(sharpeRatio, 2)}
          </div>
          <p className="text-xs text-muted-foreground">Risk-adjusted return</p>
        </CardContent>
      </Card>

      {/* Max Drawdown */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Max Drawdown</CardTitle>
          <Activity className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div
            className={`text-2xl font-bold ${getDrawdownColor(maxDrawdown)}`}
          >
            {formatPercent(maxDrawdown, 2)}
          </div>
          <p className="text-xs text-muted-foreground">Peak to trough</p>
        </CardContent>
      </Card>
    </div>
  );
}

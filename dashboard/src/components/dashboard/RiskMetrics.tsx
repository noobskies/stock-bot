import { Shield, AlertCircle, TrendingDown, Users } from "lucide-react";
import { usePortfolio } from "@/lib/hooks/usePortfolio";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { LoadingSpinner } from "@/components/shared/LoadingSpinner";
import { ErrorMessage } from "@/components/shared/ErrorMessage";
import { formatPercent } from "@/lib/utils/format";

export function RiskMetrics() {
  const { data: portfolio, isLoading, error, refetch } = usePortfolio();

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Risk Metrics</CardTitle>
        </CardHeader>
        <CardContent>
          <LoadingSpinner size="lg" text="Loading risk metrics..." />
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Risk Metrics</CardTitle>
        </CardHeader>
        <CardContent>
          <ErrorMessage error={error} retry={refetch} />
        </CardContent>
      </Card>
    );
  }

  const riskMetrics = portfolio?.risk;
  const totalExposure = riskMetrics?.total_exposure ?? 0;
  const positionCount = riskMetrics?.position_count ?? 0;
  const maxPositions = riskMetrics?.max_positions ?? 5;
  const dailyLossLimit = riskMetrics?.daily_loss_limit ?? 0;
  const circuitBreakerActive = riskMetrics?.circuit_breaker_active ?? false;

  // Calculate percentages for progress bars
  const exposurePercent = totalExposure * 100;
  const positionPercent = (positionCount / maxPositions) * 100;
  const lossPercent = Math.abs(dailyLossLimit) * 100; // Convert to positive for display

  // Determine colors based on thresholds
  const getProgressColor = (percent: number) => {
    if (percent >= 95) return "bg-red-500";
    if (percent >= 80) return "bg-yellow-500";
    return "bg-green-500";
  };

  const exposureColor = getProgressColor(exposurePercent);
  const positionColor = getProgressColor(positionPercent);
  const lossColor = getProgressColor(lossPercent);

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>Risk Metrics</CardTitle>
          {circuitBreakerActive && (
            <div className="flex items-center gap-2 text-red-500">
              <AlertCircle className="h-4 w-4" />
              <span className="text-sm font-medium">
                Circuit Breaker Active
              </span>
            </div>
          )}
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Total Exposure */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Shield className="h-4 w-4 text-muted-foreground" />
              <span className="text-sm font-medium">Total Exposure</span>
            </div>
            <span className="text-sm font-bold">
              {formatPercent(totalExposure, 1)}
            </span>
          </div>
          <Progress
            value={exposurePercent}
            className={`h-2 ${exposureColor}`}
          />
          <p className="text-xs text-muted-foreground">
            Maximum: 20% of portfolio
          </p>
        </div>

        {/* Position Count */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Users className="h-4 w-4 text-muted-foreground" />
              <span className="text-sm font-medium">Active Positions</span>
            </div>
            <span className="text-sm font-bold">
              {positionCount} / {maxPositions}
            </span>
          </div>
          <Progress
            value={positionPercent}
            className={`h-2 ${positionColor}`}
          />
          <p className="text-xs text-muted-foreground">
            Maximum: {maxPositions} concurrent positions
          </p>
        </div>

        {/* Daily Loss */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <TrendingDown className="h-4 w-4 text-muted-foreground" />
              <span className="text-sm font-medium">Daily Loss</span>
            </div>
            <span className="text-sm font-bold">
              {formatPercent(dailyLossLimit, 2)}
            </span>
          </div>
          <Progress value={lossPercent} className={`h-2 ${lossColor}`} />
          <p className="text-xs text-muted-foreground">
            Maximum: -5% daily loss limit
          </p>
        </div>
      </CardContent>
    </Card>
  );
}

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { formatConfidence } from "@/lib/utils/format";
import type { TradingSignal } from "@/types";
import {
  ActivityIcon,
  TrendingUpIcon,
  TargetIcon,
  ZapIcon,
} from "lucide-react";

interface SignalStatsProps {
  signals: TradingSignal[];
}

export function SignalStats({ signals }: SignalStatsProps) {
  // Ensure signals is an array
  const safeSignals = Array.isArray(signals) ? signals : [];

  // Calculate statistics
  const totalSignals = safeSignals.length;
  const highConfidenceSignals = safeSignals.filter((s) => s.confidence >= 80);
  const mediumConfidenceSignals = safeSignals.filter(
    (s) => s.confidence >= 70 && s.confidence < 80
  );
  const longSignals = safeSignals.filter(
    (s) => s.signal_type === "BUY" || s.signal_type === "LONG"
  );

  const avgConfidence =
    safeSignals.length > 0
      ? safeSignals.reduce((sum, s) => sum + s.confidence, 0) /
        safeSignals.length
      : 0;

  const longPercentage =
    safeSignals.length > 0
      ? (longSignals.length / safeSignals.length) * 100
      : 0;

  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Total Signals</CardTitle>
          <ActivityIcon className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{totalSignals}</div>
          <p className="text-xs text-muted-foreground">
            {longSignals.length} long, {totalSignals - longSignals.length} short
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Avg Confidence</CardTitle>
          <TargetIcon className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">
            {formatConfidence(avgConfidence)}
          </div>
          <p className="text-xs text-muted-foreground">Across all signals</p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">High Confidence</CardTitle>
          <ZapIcon className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold text-green-600">
            {highConfidenceSignals.length}
          </div>
          <p className="text-xs text-muted-foreground">
            {mediumConfidenceSignals.length} medium confidence
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Long Bias</CardTitle>
          <TrendingUpIcon className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{longPercentage.toFixed(0)}%</div>
          <p className="text-xs text-muted-foreground">
            {longSignals.length} of {totalSignals} signals
          </p>
        </CardContent>
      </Card>
    </div>
  );
}

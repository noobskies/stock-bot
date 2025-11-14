import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { formatCurrency, formatPercent, getPnlColor } from "@/lib/utils/format";
import type { Trade } from "@/types";
import {
  TrendingUpIcon,
  TrendingDownIcon,
  ActivityIcon,
  DollarSignIcon,
} from "lucide-react";

interface TradeStatsProps {
  trades: Trade[];
}

export function TradeStats({ trades }: TradeStatsProps) {
  // Ensure trades is an array
  const safeTrades = Array.isArray(trades) ? trades : [];

  // Calculate statistics
  const totalTrades = safeTrades.length;
  const closedTrades = safeTrades.filter((t) => t.exit_time !== null);
  const profitableTrades = closedTrades.filter((t) => t.pnl > 0);
  const winRate =
    closedTrades.length > 0
      ? (profitableTrades.length / closedTrades.length) * 100
      : 0;

  const totalPnl = closedTrades.reduce((sum, t) => sum + t.pnl, 0);
  const avgGain =
    profitableTrades.length > 0
      ? profitableTrades.reduce((sum, t) => sum + t.pnl, 0) /
        profitableTrades.length
      : 0;
  const losingTrades = closedTrades.filter((t) => t.pnl < 0);
  const avgLoss =
    losingTrades.length > 0
      ? losingTrades.reduce((sum, t) => sum + t.pnl, 0) / losingTrades.length
      : 0;

  const winRateColor =
    winRate >= 60
      ? "text-green-600"
      : winRate >= 50
      ? "text-yellow-600"
      : "text-red-600";

  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Total Trades</CardTitle>
          <ActivityIcon className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{totalTrades}</div>
          <p className="text-xs text-muted-foreground">
            {closedTrades.length} closed, {totalTrades - closedTrades.length}{" "}
            active
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Win Rate</CardTitle>
          <TrendingUpIcon className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className={`text-2xl font-bold ${winRateColor}`}>
            {formatPercent(winRate / 100)}
          </div>
          <p className="text-xs text-muted-foreground">
            {profitableTrades.length} wins / {closedTrades.length} closed
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Avg Gain / Loss</CardTitle>
          <DollarSignIcon className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-2">
            <span className="text-lg font-bold text-green-600">
              {formatCurrency(avgGain)}
            </span>
            <span className="text-muted-foreground">/</span>
            <span className="text-lg font-bold text-red-600">
              {formatCurrency(Math.abs(avgLoss))}
            </span>
          </div>
          <p className="text-xs text-muted-foreground">Average per trade</p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Total P&L</CardTitle>
          <TrendingDownIcon className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className={`text-2xl font-bold ${getPnlColor(totalPnl)}`}>
            {formatCurrency(totalPnl)}
          </div>
          <p className="text-xs text-muted-foreground">Closed trades only</p>
        </CardContent>
      </Card>
    </div>
  );
}

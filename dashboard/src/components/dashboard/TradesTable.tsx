import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { TableRowSkeleton } from "@/components/shared/TableRowSkeleton";
import { EmptyState } from "@/components/shared/EmptyState";
import {
  formatCurrency,
  formatPercent,
  formatDate,
  formatDuration,
  getPnlColor,
} from "@/lib/utils/format";
import type { Trade } from "@/types";
import { ArrowUpIcon, ArrowDownIcon, TrendingUp } from "lucide-react";

interface TradesTableProps {
  trades: Trade[];
  isLoading?: boolean;
}

export function TradesTable({ trades, isLoading }: TradesTableProps) {
  if (isLoading) {
    return (
      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Timestamp</TableHead>
              <TableHead>Symbol</TableHead>
              <TableHead>Side</TableHead>
              <TableHead className="text-right">Quantity</TableHead>
              <TableHead className="text-right">Entry Price</TableHead>
              <TableHead className="text-right">Exit Price</TableHead>
              <TableHead className="text-right">P&L ($)</TableHead>
              <TableHead className="text-right">P&L (%)</TableHead>
              <TableHead>Status</TableHead>
              <TableHead className="text-right">Duration</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            <TableRowSkeleton columnCount={10} rowCount={8} />
          </TableBody>
        </Table>
      </div>
    );
  }

  // Ensure trades is an array
  const safeTrades = Array.isArray(trades) ? trades : [];

  if (safeTrades.length === 0) {
    return (
      <EmptyState
        icon={TrendingUp}
        title="No Trades Yet"
        description="No trades match the current filters. Try adjusting your filters or wait for new trades."
      />
    );
  }

  return (
    <div className="rounded-md border">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Timestamp</TableHead>
            <TableHead>Symbol</TableHead>
            <TableHead>Side</TableHead>
            <TableHead className="text-right">Quantity</TableHead>
            <TableHead className="text-right">Entry Price</TableHead>
            <TableHead className="text-right">Exit Price</TableHead>
            <TableHead className="text-right">P&L ($)</TableHead>
            <TableHead className="text-right">P&L (%)</TableHead>
            <TableHead>Status</TableHead>
            <TableHead className="text-right">Duration</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {safeTrades.map((trade) => {
            const pnlColor = getPnlColor(trade.pnl);
            const isLong = trade.action.toUpperCase() === "BUY";

            return (
              <TableRow key={trade.id}>
                <TableCell className="font-medium">
                  {formatDate(trade.entry_time)}
                </TableCell>
                <TableCell>
                  <span className="font-semibold">{trade.symbol}</span>
                </TableCell>
                <TableCell>
                  <div className="flex items-center gap-1">
                    {isLong ? (
                      <ArrowUpIcon className="h-4 w-4 text-green-500" />
                    ) : (
                      <ArrowDownIcon className="h-4 w-4 text-red-500" />
                    )}
                    <Badge variant={isLong ? "default" : "secondary"}>
                      {trade.action.toUpperCase()}
                    </Badge>
                  </div>
                </TableCell>
                <TableCell className="text-right">{trade.quantity}</TableCell>
                <TableCell className="text-right">
                  {formatCurrency(trade.entry_price)}
                </TableCell>
                <TableCell className="text-right">
                  {trade.exit_price ? formatCurrency(trade.exit_price) : "-"}
                </TableCell>
                <TableCell className={`text-right font-semibold ${pnlColor}`}>
                  {trade.pnl !== null ? formatCurrency(trade.pnl) : "-"}
                </TableCell>
                <TableCell className={`text-right font-semibold ${pnlColor}`}>
                  {trade.pnl_percent !== null
                    ? formatPercent(trade.pnl_percent / 100)
                    : "-"}
                </TableCell>
                <TableCell>
                  <Badge
                    variant={
                      trade.status === "FILLED"
                        ? "default"
                        : trade.status === "CANCELLED"
                        ? "destructive"
                        : "secondary"
                    }
                  >
                    {trade.status}
                  </Badge>
                </TableCell>
                <TableCell className="text-right text-sm text-muted-foreground">
                  {trade.exit_time
                    ? formatDuration(
                        new Date(trade.exit_time).getTime() -
                          new Date(trade.entry_time).getTime()
                      )
                    : "Active"}
                </TableCell>
              </TableRow>
            );
          })}
        </TableBody>
      </Table>
    </div>
  );
}

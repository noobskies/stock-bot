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
import { formatDate, formatConfidence } from "@/lib/utils/format";
import type { TradingSignal } from "@/types";
import { ArrowUpIcon, ArrowDownIcon, TrendingUp } from "lucide-react";

interface SignalsTableProps {
  signals: TradingSignal[];
  isLoading?: boolean;
}

export function SignalsTable({ signals, isLoading }: SignalsTableProps) {
  if (isLoading) {
    return (
      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Timestamp</TableHead>
              <TableHead>Symbol</TableHead>
              <TableHead>Direction</TableHead>
              <TableHead className="text-right">Confidence</TableHead>
              <TableHead className="text-right">Entry Price</TableHead>
              <TableHead className="text-right">Quantity</TableHead>
              <TableHead>Prediction</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            <TableRowSkeleton columnCount={7} rowCount={5} />
          </TableBody>
        </Table>
      </div>
    );
  }

  // Ensure signals is an array
  const safeSignals = Array.isArray(signals) ? signals : [];

  if (safeSignals.length === 0) {
    return (
      <EmptyState
        icon={TrendingUp}
        title="No Signals Yet"
        description="No signals match the current filters. Try adjusting your filters or wait for new signals."
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
            <TableHead>Direction</TableHead>
            <TableHead className="text-right">Confidence</TableHead>
            <TableHead className="text-right">Entry Price</TableHead>
            <TableHead className="text-right">Quantity</TableHead>
            <TableHead>Prediction</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {safeSignals.map((signal) => {
            const isLong =
              signal.signal_type === "BUY" || signal.signal_type === "LONG";
            const confidenceColor =
              signal.confidence >= 80
                ? "text-green-600"
                : signal.confidence >= 70
                ? "text-yellow-600"
                : "text-muted-foreground";

            return (
              <TableRow key={signal.id}>
                <TableCell className="font-medium">
                  {formatDate(signal.timestamp)}
                </TableCell>
                <TableCell>
                  <span className="font-semibold">{signal.symbol}</span>
                </TableCell>
                <TableCell>
                  <div className="flex items-center gap-1">
                    {isLong ? (
                      <ArrowUpIcon className="h-4 w-4 text-green-500" />
                    ) : (
                      <ArrowDownIcon className="h-4 w-4 text-red-500" />
                    )}
                    <Badge variant={isLong ? "default" : "secondary"}>
                      {signal.signal_type}
                    </Badge>
                  </div>
                </TableCell>
                <TableCell
                  className={`text-right font-semibold ${confidenceColor}`}
                >
                  {formatConfidence(signal.confidence)}
                </TableCell>
                <TableCell className="text-right">
                  ${signal.entry_price.toFixed(2)}
                </TableCell>
                <TableCell className="text-right">
                  {signal.suggested_quantity}
                </TableCell>
                <TableCell>
                  <span className="text-sm text-muted-foreground">
                    {signal.predicted_direction}
                  </span>
                </TableCell>
              </TableRow>
            );
          })}
        </TableBody>
      </Table>
    </div>
  );
}

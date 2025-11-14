import { ArrowUpDown, Inbox } from "lucide-react";
import { usePortfolio } from "@/lib/hooks/usePortfolio";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { LoadingSpinner } from "@/components/shared/LoadingSpinner";
import { ErrorMessage } from "@/components/shared/ErrorMessage";
import { EmptyState } from "@/components/shared/EmptyState";
import { formatCurrency, formatPercent, getPnlColor } from "@/lib/utils/format";

export function PositionsTable() {
  const { data: portfolio, isLoading, error, refetch } = usePortfolio();

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Active Positions</CardTitle>
          <CardDescription>Current open positions</CardDescription>
        </CardHeader>
        <CardContent>
          <LoadingSpinner size="lg" text="Loading positions..." />
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Active Positions</CardTitle>
        </CardHeader>
        <CardContent>
          <ErrorMessage error={error} retry={refetch} />
        </CardContent>
      </Card>
    );
  }

  const positions = portfolio?.positions ?? [];

  if (positions.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Active Positions</CardTitle>
          <CardDescription>Current open positions</CardDescription>
        </CardHeader>
        <CardContent>
          <EmptyState
            icon={Inbox}
            title="No Active Positions"
            description="You don't have any open positions at the moment."
          />
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Active Positions</CardTitle>
        <CardDescription>
          {positions.length} open position{positions.length !== 1 ? "s" : ""}
        </CardDescription>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>
                <Button variant="ghost" size="sm" className="h-8 p-0">
                  Symbol
                  <ArrowUpDown className="ml-2 h-3 w-3" />
                </Button>
              </TableHead>
              <TableHead className="text-right">Quantity</TableHead>
              <TableHead className="text-right">Entry Price</TableHead>
              <TableHead className="text-right">Current Price</TableHead>
              <TableHead className="text-right">P&L ($)</TableHead>
              <TableHead className="text-right">P&L (%)</TableHead>
              <TableHead className="text-right">Stop Loss</TableHead>
              <TableHead className="text-right">Trailing Stop</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {positions.map((position) => {
              const pnlColor = getPnlColor(position.unrealized_pnl);

              return (
                <TableRow key={position.symbol}>
                  <TableCell className="font-medium">
                    {position.symbol}
                  </TableCell>
                  <TableCell className="text-right">
                    {position.quantity}
                  </TableCell>
                  <TableCell className="text-right">
                    {formatCurrency(position.entry_price)}
                  </TableCell>
                  <TableCell className="text-right">
                    {formatCurrency(position.current_price)}
                  </TableCell>
                  <TableCell className={`text-right font-medium ${pnlColor}`}>
                    {formatCurrency(position.unrealized_pnl)}
                  </TableCell>
                  <TableCell className={`text-right font-medium ${pnlColor}`}>
                    {formatPercent(position.unrealized_pnl_percent, 2)}
                  </TableCell>
                  <TableCell className="text-right">
                    {position.stop_loss
                      ? formatCurrency(position.stop_loss)
                      : "-"}
                  </TableCell>
                  <TableCell className="text-right">
                    {position.trailing_stop
                      ? formatCurrency(position.trailing_stop)
                      : "-"}
                  </TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}

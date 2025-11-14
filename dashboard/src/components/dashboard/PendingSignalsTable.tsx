import { Check, X, TrendingUp, TrendingDown, Bell } from "lucide-react";
import { useSignals } from "@/lib/hooks/useSignals";
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
import { Badge } from "@/components/ui/badge";
import { LoadingSpinner } from "@/components/shared/LoadingSpinner";
import { ErrorMessage } from "@/components/shared/ErrorMessage";
import { EmptyState } from "@/components/shared/EmptyState";
import { formatConfidence, formatDateShort } from "@/lib/utils/format";

export function PendingSignalsTable() {
  const {
    signals,
    isLoading,
    error,
    approve,
    reject,
    isApproving,
    isRejecting,
  } = useSignals();

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Pending Signals</CardTitle>
          <CardDescription>Signals awaiting approval</CardDescription>
        </CardHeader>
        <CardContent>
          <LoadingSpinner size="lg" text="Loading signals..." />
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Pending Signals</CardTitle>
        </CardHeader>
        <CardContent>
          <ErrorMessage error={error} />
        </CardContent>
      </Card>
    );
  }

  if (!signals || signals.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Pending Signals</CardTitle>
          <CardDescription>Signals awaiting approval</CardDescription>
        </CardHeader>
        <CardContent>
          <EmptyState
            icon={Bell}
            title="No Pending Signals"
            description="There are no trading signals awaiting your approval."
          />
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Pending Signals</CardTitle>
        <CardDescription>
          {signals.length} signal{signals.length !== 1 ? "s" : ""} awaiting
          approval
        </CardDescription>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Symbol</TableHead>
              <TableHead>Direction</TableHead>
              <TableHead>Confidence</TableHead>
              <TableHead>Time</TableHead>
              <TableHead className="text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {signals.map((signal) => {
              const isLong =
                signal.signal_type === "LONG" || signal.signal_type === "BUY";
              const DirectionIcon = isLong ? TrendingUp : TrendingDown;
              const directionColor = isLong ? "text-green-500" : "text-red-500";
              const directionText = signal.signal_type;

              return (
                <TableRow key={signal.id}>
                  <TableCell className="font-medium">{signal.symbol}</TableCell>
                  <TableCell>
                    <div
                      className={`flex items-center gap-1 ${directionColor}`}
                    >
                      <DirectionIcon className="h-4 w-4" />
                      <span className="font-medium">{directionText}</span>
                    </div>
                  </TableCell>
                  <TableCell>
                    <Badge variant="outline">
                      {formatConfidence(signal.confidence)}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-muted-foreground">
                    {formatDateShort(signal.timestamp)}
                  </TableCell>
                  <TableCell className="text-right">
                    <div className="flex justify-end gap-2">
                      <Button
                        size="sm"
                        variant="default"
                        onClick={() => approve(signal.id)}
                        disabled={isApproving || isRejecting}
                      >
                        {isApproving ? (
                          <LoadingSpinner size="sm" />
                        ) : (
                          <>
                            <Check className="mr-1 h-3 w-3" />
                            Approve
                          </>
                        )}
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => reject(signal.id)}
                        disabled={isApproving || isRejecting}
                      >
                        {isRejecting ? (
                          <LoadingSpinner size="sm" />
                        ) : (
                          <>
                            <X className="mr-1 h-3 w-3" />
                            Reject
                          </>
                        )}
                      </Button>
                    </div>
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

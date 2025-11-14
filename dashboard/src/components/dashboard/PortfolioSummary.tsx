import { DollarSign, TrendingUp, Wallet, CreditCard } from "lucide-react";
import { usePortfolio } from "@/lib/hooks/usePortfolio";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { LoadingSpinner } from "@/components/shared/LoadingSpinner";
import { ErrorMessage } from "@/components/shared/ErrorMessage";
import { formatCurrency, formatPercent, getPnlColor } from "@/lib/utils/format";

export function PortfolioSummary() {
  const { data: portfolio, isLoading, error, refetch } = usePortfolio();

  if (isLoading) {
    return (
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
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
          <CardTitle>Portfolio Summary</CardTitle>
        </CardHeader>
        <CardContent>
          <ErrorMessage error={error} retry={refetch} />
        </CardContent>
      </Card>
    );
  }

  const portfolioValue = portfolio?.portfolio.total_value ?? 0;
  const dailyPnl = portfolio?.portfolio.daily_pnl ?? 0;
  const dailyPnlPercent = portfolio?.portfolio.daily_pnl_percent ?? 0;
  const cashAvailable = portfolio?.portfolio.cash ?? 0;
  const buyingPower = portfolio?.portfolio.buying_power ?? 0;

  const pnlColor = getPnlColor(dailyPnl);

  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
      {/* Portfolio Value */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Portfolio Value</CardTitle>
          <DollarSign className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">
            {formatCurrency(portfolioValue)}
          </div>
          <p className="text-xs text-muted-foreground">Total account value</p>
        </CardContent>
      </Card>

      {/* Daily P&L */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Daily P&L</CardTitle>
          <TrendingUp className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className={`text-2xl font-bold ${pnlColor}`}>
            {formatCurrency(dailyPnl)}
          </div>
          <p className={`text-xs ${pnlColor}`}>
            {formatPercent(dailyPnlPercent, 2)} today
          </p>
        </CardContent>
      </Card>

      {/* Cash Available */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Cash Available</CardTitle>
          <Wallet className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">
            {formatCurrency(cashAvailable)}
          </div>
          <p className="text-xs text-muted-foreground">Available to trade</p>
        </CardContent>
      </Card>

      {/* Buying Power */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Buying Power</CardTitle>
          <CreditCard className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">
            {formatCurrency(buyingPower)}
          </div>
          <p className="text-xs text-muted-foreground">Margin + cash</p>
        </CardContent>
      </Card>
    </div>
  );
}

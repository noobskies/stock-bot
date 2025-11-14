import { PortfolioSummary } from "@/components/dashboard/PortfolioSummary";
import { RiskMetrics } from "@/components/dashboard/RiskMetrics";
import { PerformanceCards } from "@/components/dashboard/PerformanceCards";
import { BotControls } from "@/components/dashboard/BotControls";
import { PositionsTable } from "@/components/dashboard/PositionsTable";
import { PendingSignalsTable } from "@/components/dashboard/PendingSignalsTable";

export function DashboardPage() {
  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
        <p className="text-muted-foreground">
          Portfolio overview and active positions
        </p>
      </div>

      {/* Portfolio Summary Cards */}
      <PortfolioSummary />

      {/* Two Column Layout */}
      <div className="grid gap-6 lg:grid-cols-3">
        {/* Left Column - 2/3 width */}
        <div className="space-y-6 lg:col-span-2">
          {/* Active Positions */}
          <PositionsTable />

          {/* Pending Signals */}
          <PendingSignalsTable />
        </div>

        {/* Right Column - 1/3 width */}
        <div className="space-y-6">
          {/* Bot Controls */}
          <BotControls />

          {/* Risk Metrics */}
          <RiskMetrics />

          {/* Performance Cards */}
          <PerformanceCards />
        </div>
      </div>
    </div>
  );
}

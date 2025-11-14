import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { RefreshCwIcon } from "lucide-react";
import { Checkbox } from "@/components/ui/checkbox";
import type { TradeFilters as TradeFiltersType } from "@/types";

interface TradeFiltersProps {
  filters: TradeFiltersType;
  onFilterChange: (filters: TradeFiltersType) => void;
  onReset: () => void;
}

export function TradeFilters({
  filters,
  onFilterChange,
  onReset,
}: TradeFiltersProps) {
  const handleSymbolChange = (value: string) => {
    onFilterChange({
      ...filters,
      symbol: value === "all" ? undefined : value,
    });
  };

  const handleStatusChange = (value: string) => {
    onFilterChange({
      ...filters,
      status: value === "all" ? undefined : value,
    });
  };

  const handleSideChange = (value: string) => {
    onFilterChange({
      ...filters,
      side: value === "all" ? undefined : value,
    });
  };

  const handleDateRangeChange = (value: string) => {
    const now = new Date();
    let startDate: Date | undefined;

    switch (value) {
      case "today":
        startDate = new Date(now.setHours(0, 0, 0, 0));
        break;
      case "week":
        startDate = new Date(now.setDate(now.getDate() - 7));
        break;
      case "month":
        startDate = new Date(now.setMonth(now.getMonth() - 1));
        break;
      case "all":
      default:
        startDate = undefined;
    }

    onFilterChange({
      ...filters,
      startDate: startDate?.toISOString(),
      endDate: undefined,
    });
  };

  const handleArchivedChange = (checked: boolean) => {
    onFilterChange({
      ...filters,
      include_archived: checked,
    });
  };

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-end gap-4 rounded-lg border p-4 bg-card">
        <div className="flex-1 min-w-[150px]">
          <Label htmlFor="symbol-filter">Symbol</Label>
          <Select
            value={filters.symbol || "all"}
            onValueChange={handleSymbolChange}
          >
            <SelectTrigger id="symbol-filter">
              <SelectValue placeholder="All Symbols" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Symbols</SelectItem>
              <SelectItem value="PLTR">PLTR</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div className="flex-1 min-w-[150px]">
          <Label htmlFor="status-filter">Status</Label>
          <Select
            value={filters.status || "all"}
            onValueChange={handleStatusChange}
          >
            <SelectTrigger id="status-filter">
              <SelectValue placeholder="All Statuses" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Statuses</SelectItem>
              <SelectItem value="open">Open/Active</SelectItem>
              <SelectItem value="FILLED">Filled</SelectItem>
              <SelectItem value="PENDING">Pending</SelectItem>
              <SelectItem value="CANCELLED">Cancelled</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div className="flex-1 min-w-[150px]">
          <Label htmlFor="side-filter">Side</Label>
          <Select
            value={filters.side || "all"}
            onValueChange={handleSideChange}
          >
            <SelectTrigger id="side-filter">
              <SelectValue placeholder="All Sides" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Sides</SelectItem>
              <SelectItem value="BUY">Buy</SelectItem>
              <SelectItem value="SELL">Sell</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div className="flex-1 min-w-[150px]">
          <Label htmlFor="date-filter">Date Range</Label>
          <Select
            value={
              filters.startDate
                ? filters.startDate.includes(
                    new Date().toISOString().split("T")[0]
                  )
                  ? "today"
                  : "week"
                : "all"
            }
            onValueChange={handleDateRangeChange}
          >
            <SelectTrigger id="date-filter">
              <SelectValue placeholder="All Time" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Time</SelectItem>
              <SelectItem value="today">Today</SelectItem>
              <SelectItem value="week">Last 7 Days</SelectItem>
              <SelectItem value="month">Last 30 Days</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <Button variant="outline" onClick={onReset} className="gap-2">
          <RefreshCwIcon className="h-4 w-4" />
          Reset
        </Button>
      </div>

      <div className="flex items-center space-x-2 px-4">
        <Checkbox
          id="archived-trades"
          checked={filters.include_archived || false}
          onCheckedChange={handleArchivedChange}
        />
        <Label
          htmlFor="archived-trades"
          className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70 cursor-pointer"
        >
          Show archived trades
        </Label>
      </div>
    </div>
  );
}

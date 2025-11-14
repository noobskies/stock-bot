import { Link, useLocation } from "react-router-dom";
import { Activity, TrendingUp } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useBotStatus, useBotControl } from "@/lib/hooks/useBotControl";

export function Navbar() {
  const location = useLocation();
  const { data: status, isLoading: statusLoading } = useBotStatus();
  const { start, stop, isStarting, isStopping } = useBotControl();

  const isActive = (path: string) => {
    return location.pathname === path;
  };

  const getBadgeVariant = () => {
    if (statusLoading) return "secondary";
    if (!status) return "secondary";

    return status.is_running ? "default" : "secondary";
  };

  const getStatusText = () => {
    if (statusLoading) return "Loading...";
    if (!status) return "Unknown";

    return status.is_running ? "Active" : "Stopped";
  };

  const handleStart = () => {
    start();
  };

  const handleStop = () => {
    stop();
  };

  return (
    <nav className="border-b bg-background sticky top-0 z-50">
      <div className="container mx-auto px-4 max-w-7xl">
        <div className="flex h-16 items-center justify-between">
          {/* Logo and brand */}
          <div className="flex items-center gap-2">
            <TrendingUp className="h-6 w-6 text-primary" />
            <span className="text-xl font-bold">Stock Trading Bot</span>
          </div>

          {/* Navigation links */}
          <div className="flex items-center gap-6">
            <Link
              to="/"
              className={`text-sm font-medium transition-colors hover:text-primary ${
                isActive("/") ? "text-foreground" : "text-muted-foreground"
              }`}
            >
              Dashboard
            </Link>
            <Link
              to="/trades"
              className={`text-sm font-medium transition-colors hover:text-primary ${
                isActive("/trades")
                  ? "text-foreground"
                  : "text-muted-foreground"
              }`}
            >
              Trades
            </Link>
            <Link
              to="/signals"
              className={`text-sm font-medium transition-colors hover:text-primary ${
                isActive("/signals")
                  ? "text-foreground"
                  : "text-muted-foreground"
              }`}
            >
              Signals
            </Link>
            <Link
              to="/settings"
              className={`text-sm font-medium transition-colors hover:text-primary ${
                isActive("/settings")
                  ? "text-foreground"
                  : "text-muted-foreground"
              }`}
            >
              Settings
            </Link>
          </div>

          {/* Bot status and controls */}
          <div className="flex items-center gap-3">
            {/* Status badge */}
            <div className="flex items-center gap-2">
              <Activity className="h-4 w-4 text-muted-foreground" />
              <Badge variant={getBadgeVariant()}>{getStatusText()}</Badge>
            </div>

            {/* Control buttons */}
            {status?.is_running ? (
              <Button
                size="sm"
                variant="outline"
                onClick={handleStop}
                disabled={isStopping}
              >
                {isStopping ? "Stopping..." : "Stop Bot"}
              </Button>
            ) : (
              <Button size="sm" onClick={handleStart} disabled={isStarting}>
                {isStarting ? "Starting..." : "Start Bot"}
              </Button>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
}

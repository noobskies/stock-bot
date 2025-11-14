import { useState } from "react";
import { Play, Square, AlertTriangle, RefreshCw } from "lucide-react";
import { useBotStatus, useBotControl } from "@/lib/hooks/useBotControl";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { LoadingSpinner } from "@/components/shared/LoadingSpinner";
import { ErrorMessage } from "@/components/shared/ErrorMessage";
import { ConfirmDialog } from "@/components/shared/ConfirmDialog";

export function BotControls() {
  const { data: status, isLoading, error, refetch } = useBotStatus();
  const {
    start,
    stop,
    setMode,
    emergencyStop,
    sync,
    isStarting,
    isStopping,
    isEmergencyStopping,
    isSettingMode,
    isSyncing,
  } = useBotControl();

  const [showStopConfirm, setShowStopConfirm] = useState(false);
  const [showEmergencyConfirm, setShowEmergencyConfirm] = useState(false);

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Bot Controls</CardTitle>
        </CardHeader>
        <CardContent>
          <LoadingSpinner size="lg" text="Loading bot status..." />
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Bot Controls</CardTitle>
        </CardHeader>
        <CardContent>
          <ErrorMessage error={error} retry={refetch} />
        </CardContent>
      </Card>
    );
  }

  const isRunning = status?.is_running ?? false;
  const mode = status?.mode ?? "unknown";

  const getStatusBadgeVariant = () => {
    if (isRunning) return "default"; // green
    return "secondary"; // gray
  };

  const getStatusText = () => {
    if (isRunning) return "Active";
    return "Stopped";
  };

  return (
    <>
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Bot Controls</CardTitle>
              <CardDescription>
                Manage bot operation and trading mode
              </CardDescription>
            </div>
            <Badge variant={getStatusBadgeVariant()}>{getStatusText()}</Badge>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Start/Stop Controls */}
          <div className="flex gap-2">
            {!isRunning ? (
              <Button
                onClick={() => start()}
                disabled={isStarting}
                className="flex-1"
              >
                {isStarting ? (
                  <LoadingSpinner size="sm" />
                ) : (
                  <>
                    <Play className="mr-2 h-4 w-4" />
                    Start Bot
                  </>
                )}
              </Button>
            ) : (
              <Button
                onClick={() => setShowStopConfirm(true)}
                variant="outline"
                disabled={isStopping}
                className="flex-1"
              >
                {isStopping ? (
                  <LoadingSpinner size="sm" />
                ) : (
                  <>
                    <Square className="mr-2 h-4 w-4" />
                    Stop Bot
                  </>
                )}
              </Button>
            )}

            <Button
              onClick={() => setShowEmergencyConfirm(true)}
              variant="destructive"
              disabled={isEmergencyStopping || !isRunning}
            >
              {isEmergencyStopping ? (
                <LoadingSpinner size="sm" />
              ) : (
                <>
                  <AlertTriangle className="mr-2 h-4 w-4" />
                  Emergency Stop
                </>
              )}
            </Button>
          </div>

          {/* Trading Mode Selector */}
          <div className="space-y-2">
            <label className="text-sm font-medium">Trading Mode</label>
            <Select
              value={mode}
              onValueChange={(value) =>
                setMode(value as "auto" | "manual" | "hybrid")
              }
              disabled={isSettingMode}
            >
              <SelectTrigger>
                <SelectValue placeholder="Select mode" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="auto">Auto (confidence &gt; 80%)</SelectItem>
                <SelectItem value="manual">
                  Manual (all signals require approval)
                </SelectItem>
                <SelectItem value="hybrid">
                  Hybrid (auto &gt; 80%, manual 70-80%)
                </SelectItem>
              </SelectContent>
            </Select>
            <p className="text-xs text-muted-foreground">
              {mode === "auto" &&
                "Bot executes high-confidence signals automatically"}
              {mode === "manual" && "All signals require manual approval"}
              {mode === "hybrid" &&
                "High-confidence signals execute automatically, medium-confidence require approval"}
            </p>
          </div>

          {/* Sync Button */}
          <Button
            onClick={() => sync()}
            variant="outline"
            disabled={isSyncing}
            className="w-full"
          >
            {isSyncing ? (
              <LoadingSpinner size="sm" />
            ) : (
              <>
                <RefreshCw className="mr-2 h-4 w-4" />
                Sync with Broker
              </>
            )}
          </Button>
        </CardContent>
      </Card>

      {/* Stop Confirmation Dialog */}
      <ConfirmDialog
        open={showStopConfirm}
        onOpenChange={setShowStopConfirm}
        title="Stop Trading Bot?"
        description="This will stop all trading activity. Active positions will remain open but no new trades will be executed."
        onConfirm={() => {
          stop();
          setShowStopConfirm(false);
        }}
      />

      {/* Emergency Stop Confirmation Dialog */}
      <ConfirmDialog
        open={showEmergencyConfirm}
        onOpenChange={setShowEmergencyConfirm}
        title="Emergency Stop"
        description="WARNING: This will immediately stop the bot and close all open positions at market price. This action should only be used in emergencies."
        onConfirm={() => {
          emergencyStop();
          setShowEmergencyConfirm(false);
        }}
      />
    </>
  );
}

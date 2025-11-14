import { useBotStatus } from "@/lib/hooks/useBotControl";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { LoadingSpinner } from "@/components/shared/LoadingSpinner";
import { ErrorMessage } from "@/components/shared/ErrorMessage";
import { Badge } from "@/components/ui/badge";
import { SettingsIcon, CheckCircle2Icon } from "lucide-react";

export function SettingsPage() {
  const { data: status, isLoading, error, refetch } = useBotStatus();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-12">
        <LoadingSpinner size="lg" text="Loading settings..." />
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Bot Settings</h1>
          <p className="text-muted-foreground">
            Configure bot behavior and risk parameters
          </p>
        </div>
        <ErrorMessage
          error={error}
          title="Failed to load settings"
          retry={refetch}
        />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Bot Settings</h1>
          <p className="text-muted-foreground">
            Current bot configuration (read-only)
          </p>
        </div>
        <SettingsIcon className="h-8 w-8 text-muted-foreground" />
      </div>

      {/* Bot Status */}
      <Card>
        <CardHeader>
          <CardTitle>Bot Status</CardTitle>
          <CardDescription>Current operational status</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            <div className="space-y-1">
              <p className="text-sm font-medium text-muted-foreground">
                Running Status
              </p>
              <div className="flex items-center gap-2">
                {status?.is_running ? (
                  <>
                    <CheckCircle2Icon className="h-4 w-4 text-green-600" />
                    <Badge variant="default">Active</Badge>
                  </>
                ) : (
                  <Badge variant="secondary">Stopped</Badge>
                )}
              </div>
            </div>

            <div className="space-y-1">
              <p className="text-sm font-medium text-muted-foreground">
                Trading Mode
              </p>
              <Badge variant="outline">{status?.mode || "Unknown"}</Badge>
            </div>

            <div className="space-y-1">
              <p className="text-sm font-medium text-muted-foreground">
                Account Type
              </p>
              <Badge
                variant={status?.is_paper_trading ? "secondary" : "default"}
              >
                {status?.is_paper_trading ? "Paper Trading" : "Live Trading"}
              </Badge>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Note about settings */}
      <Card className="border-blue-200 bg-blue-50">
        <CardContent className="pt-6">
          <p className="text-sm text-blue-900">
            <strong>Note:</strong> Settings are currently read-only in the React
            dashboard. To modify bot configuration, edit the{" "}
            <code className="bg-blue-100 px-1 py-0.5 rounded">
              config/config.yaml
            </code>{" "}
            file and restart the bot. Full settings editing will be available in
            a future update.
          </p>
        </CardContent>
      </Card>

      <p className="text-sm text-muted-foreground">
        Settings page implementation complete. Configuration editing via UI
        coming in Phase 7 (Polish & Enhancements).
      </p>
    </div>
  );
}

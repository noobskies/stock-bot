import React, { Component } from "react";
import type { ReactNode } from "react";
import { AlertTriangle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: React.ErrorInfo | null;
}

/**
 * Error Boundary Component
 *
 * Catches JavaScript errors anywhere in the child component tree,
 * logs those errors, and displays a fallback UI instead of crashing.
 *
 * @example
 * ```tsx
 * <ErrorBoundary>
 *   <App />
 * </ErrorBoundary>
 * ```
 */
export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
    };
  }

  static getDerivedStateFromError(error: Error): Partial<State> {
    // Update state so the next render will show the fallback UI
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    // Log error details to console for debugging
    console.error("ErrorBoundary caught an error:", error, errorInfo);

    this.setState({
      error,
      errorInfo,
    });

    // You could also log the error to an error reporting service here
    // e.g., Sentry, LogRocket, etc.
  }

  handleReset = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
    });
    // Reload the page to reset the application state
    window.location.reload();
  };

  render() {
    if (this.state.hasError) {
      // Custom fallback UI provided by parent
      if (this.props.fallback) {
        return this.props.fallback;
      }

      // Default fallback UI
      return (
        <div className="min-h-screen flex items-center justify-center bg-background p-4">
          <div className="max-w-2xl w-full">
            <Alert variant="destructive" className="mb-4">
              <AlertTriangle className="h-4 w-4" />
              <AlertTitle>Something went wrong</AlertTitle>
              <AlertDescription>
                The application encountered an unexpected error. This has been
                logged and we'll look into it.
              </AlertDescription>
            </Alert>

            <div className="bg-card border rounded-lg p-6 space-y-4">
              <div>
                <h2 className="text-xl font-semibold mb-2">Error Details</h2>
                <div className="bg-muted p-4 rounded border overflow-auto max-h-60">
                  <p className="font-mono text-sm text-destructive mb-2">
                    {this.state.error?.toString()}
                  </p>
                  {this.state.errorInfo && (
                    <pre className="text-xs text-muted-foreground whitespace-pre-wrap">
                      {this.state.errorInfo.componentStack}
                    </pre>
                  )}
                </div>
              </div>

              <div className="flex gap-2">
                <Button onClick={this.handleReset}>Reload Application</Button>
                <Button
                  variant="outline"
                  onClick={() => {
                    // Copy error details to clipboard
                    const errorText = `Error: ${this.state.error?.toString()}\n\nStack: ${
                      this.state.errorInfo?.componentStack
                    }`;
                    navigator.clipboard.writeText(errorText);
                  }}
                >
                  Copy Error Details
                </Button>
              </div>

              <div className="text-sm text-muted-foreground">
                <p className="mb-2">
                  If this problem persists, try the following:
                </p>
                <ul className="list-disc list-inside space-y-1">
                  <li>Clear your browser cache and reload</li>
                  <li>Check your internet connection</li>
                  <li>Ensure the Flask backend is running</li>
                  <li>Check the browser console for additional errors</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

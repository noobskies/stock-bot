import { AlertCircle } from "lucide-react";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";

export interface ErrorMessageProps {
  error: Error | null;
  retry?: () => void;
  title?: string;
}

export function ErrorMessage({
  error,
  retry,
  title = "Error",
}: ErrorMessageProps) {
  if (!error) return null;

  return (
    <Alert variant="destructive" className="my-4">
      <AlertCircle className="h-4 w-4" />
      <AlertTitle>{title}</AlertTitle>
      <AlertDescription className="flex flex-col gap-2">
        <p>{error.message || "An unexpected error occurred"}</p>
        {retry && (
          <Button variant="outline" size="sm" onClick={retry} className="w-fit">
            Try Again
          </Button>
        )}
      </AlertDescription>
    </Alert>
  );
}

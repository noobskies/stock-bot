import { TableCell, TableRow } from "@/components/ui/table";
import { Skeleton } from "@/components/ui/skeleton";

interface TableRowSkeletonProps {
  /** Number of columns in the table */
  columnCount: number;
  /** Number of skeleton rows to render */
  rowCount?: number;
  /** Optional custom column widths (e.g., ["w-20", "w-32", "w-16"]) */
  columnWidths?: string[];
}

/**
 * Reusable skeleton loader for table rows
 *
 * Shows shimmer effect while data is loading, matching the table structure
 *
 * @example
 * ```tsx
 * {isLoading ? (
 *   <TableRowSkeleton columnCount={6} rowCount={5} />
 * ) : (
 *   data.map(item => <TableRow key={item.id}>...</TableRow>)
 * )}
 * ```
 */
export function TableRowSkeleton({
  columnCount,
  rowCount = 5,
  columnWidths,
}: TableRowSkeletonProps) {
  return (
    <>
      {Array.from({ length: rowCount }).map((_, rowIndex) => (
        <TableRow key={rowIndex}>
          {Array.from({ length: columnCount }).map((_, colIndex) => (
            <TableCell key={colIndex}>
              <Skeleton
                className={`h-4 ${columnWidths?.[colIndex] || "w-24"}`}
              />
            </TableCell>
          ))}
        </TableRow>
      ))}
    </>
  );
}

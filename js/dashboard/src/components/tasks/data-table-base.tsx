"use client";

import * as React from "react";
import {
  ColumnDef,
  flexRender,
  Table as TableType,
} from "@tanstack/react-table";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  DataTablePagination,
  DataTablePaginationProps,
} from "@/components/ui/data-table";
import { Task } from "./data/schema";
import { TaskRow } from "./task-row";

interface DataTableProps<TData, TValue> {
  columns: ColumnDef<TData, TValue>[];
  table: TableType<TData>;
  // Customize this message to override what to display when there are no
  // results, such as if we get a React Query error.
  noResultsMessage?: string | React.ReactNode;

  // Normally, React Table expects us to know in total how many pages there are
  // and then we can call a React Table API method to see if we can get the next
  // page. When we are doing cursor-based pagination, React Table does not know
  // how many pages there are, so we can use information from the query itself
  // to inform React Table if there are more pages.
  canGetNextPageOverride?: boolean;

  totalRowsOverride?: bigint | null;

  loadingStatus?: DataTablePaginationProps<TData>["loadingStatus"];

  isDataset?: boolean;
}

export function DataTableBase<TData extends Task, TValue>({
  columns,
  table,
  noResultsMessage,
  canGetNextPageOverride,
  totalRowsOverride,
  loadingStatus,
}: DataTableProps<TData, TValue>) {
  return (
    <div className="space-y-4 flex flex-col h-full">
      <div className="rounded-md border flex-grow overflow-auto">
        <Table className="flex-grow">
          <TableHeader>
            {table.getHeaderGroups().map((headerGroup) => (
              <TableRow key={headerGroup.id}>
                {headerGroup.headers.map((header) => {
                  return (
                    <TableHead key={header.id} colSpan={header.colSpan}>
                      {header.isPlaceholder
                        ? null
                        : flexRender(
                            header.column.columnDef.header,
                            header.getContext(),
                          )}
                    </TableHead>
                  );
                })}
              </TableRow>
            ))}
          </TableHeader>
          <TableBody>
            {table.getRowModel().rows?.length ? (
              table
                .getRowModel()
                .rows.map((row, idx) => (
                  <TaskRow
                    key={row.id}
                    allRows={table.getRowModel().rows}
                    rowIndex={idx}
                  />
                ))
            ) : (
              <TableRow>
                <TableCell
                  colSpan={columns.length}
                  className="h-24 text-center"
                >
                  {noResultsMessage || "No LLM logs."}
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>
      <DataTablePagination
        table={table}
        canGetNextPageOverride={canGetNextPageOverride}
        totalRowsOverride={totalRowsOverride}
        loadingStatus={loadingStatus}
      />
    </div>
  );
}

export function useRowSelectionSyncedToAtom<TData extends Task>(
  data: TData[],
): [
  Record<string, boolean>,
  React.Dispatch<React.SetStateAction<Record<string, boolean>>>,
] {
  const [rowSelection, setRowSelection] = React.useState<
    Record<string, boolean>
  >({});

  return [rowSelection, setRowSelection];
}

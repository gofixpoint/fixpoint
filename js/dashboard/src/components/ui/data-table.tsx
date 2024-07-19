import { useState, useEffect } from "react";
import {
  ChevronLeft as ChevronLeftIcon,
  ChevronRight as ChevronRightIcon,
  ChevronsLeft as DoubleArrowLeftIcon,
  ChevronsRight as DoubleArrowRightIcon,
} from "lucide-react";
import { Table } from "@tanstack/react-table";

import { isSet } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

export interface DataTablePaginationProps<TData> {
  table: Table<TData>;
  canGetNextPageOverride?: boolean;

  // Normally, React Table expects us to know in total how many pages there are
  // and then we can call a React Table API method to see if we can get the next
  // page. When we are doing cursor-based pagination, React Table does not know
  // how many pages there are, so we can use information from the query itself
  // to inform React Table if there are more pages.
  enableLastPage?: boolean;

  totalRowsOverride?: bigint | null;

  loadingStatus?: "error" | "pending" | "success";
}

export function DataTablePagination<TData>({
  table,
  canGetNextPageOverride,
  enableLastPage,
  totalRowsOverride,
  loadingStatus,
}: DataTablePaginationProps<TData>) {
  return (
    <div className="flex items-center justify-between px-2">
      <div className="flex-1 text-sm text-muted-foreground">
        {table.getFilteredSelectedRowModel().rows.length} of{" "}
        {isSet(totalRowsOverride)
          ? totalRowsOverride.toString()
          : table.getFilteredRowModel().rows.length}{" "}
        row(s) selected.
      </div>
      <div className="flex items-center space-x-6 lg:space-x-8">
        <div className="flex items-center space-x-2">
          <p className="text-sm font-medium">Rows per page</p>
          <Select
            value={`${table.getState().pagination.pageSize}`}
            onValueChange={(value) => {
              table.setPageSize(Number(value));
            }}
          >
            <SelectTrigger className="h-8 w-[70px]">
              <SelectValue placeholder={table.getState().pagination.pageSize} />
            </SelectTrigger>
            <SelectContent side="top">
              {[10, 20, 30, 40, 50].map((pageSize) => (
                <SelectItem key={pageSize} value={`${pageSize}`}>
                  {pageSize}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <PageDisplay table={table} />
        <div className="flex items-center space-x-2">
          <Button
            variant="outline"
            className="hidden h-8 w-8 p-0 lg:flex"
            onClick={() => table.setPageIndex(0)}
            disabled={!table.getCanPreviousPage()}
          >
            <span className="sr-only">Go to first page</span>
            <DoubleArrowLeftIcon className="h-4 w-4" />
          </Button>
          <Button
            variant="outline"
            className="h-8 w-8 p-0"
            onClick={() => table.previousPage()}
            disabled={!table.getCanPreviousPage()}
          >
            <span className="sr-only">Go to previous page</span>
            <ChevronLeftIcon className="h-4 w-4" />
          </Button>
          <Button
            variant="outline"
            className="h-8 w-8 p-0"
            onClick={() => table.nextPage()}
            disabled={!canGetNextPage(table, canGetNextPageOverride)}
          >
            <span className="sr-only">Go to next page</span>
            <ChevronRightIcon className="h-4 w-4" />
          </Button>
          {/* For now, going to the last page is disabled because we are doing
          cursor-based pagination. */}
          {enableLastPage && (
            <Button
              variant="outline"
              className="hidden h-8 w-8 p-0 lg:flex"
              onClick={() => table.setPageIndex(table.getPageCount() - 1)}
              disabled={!table.getCanNextPage()}
            >
              <span className="sr-only">Go to last page</span>
              <DoubleArrowRightIcon className="h-4 w-4" />
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}

function canGetNextPage<TData>(
  table: Table<TData>,
  canGetNextPageOverride: boolean | undefined,
) {
  if (canGetNextPageOverride === undefined) {
    return table.getCanNextPage();
  }
  return canGetNextPageOverride;
}

function PageDisplay<TData>(props: { table: Table<TData> }) {
  const { table } = props;
  let txt: string;
  if (table.getPageCount() < 0) {
    txt = `Page ${table.getState().pagination.pageIndex + 1}`;
  } else {
    txt = `Page ${
      table.getState().pagination.pageIndex + 1
    } of ${table.getPageCount()}`;
  }
  return (
    <div className="flex w-[100px] items-center justify-center text-sm font-medium">
      {txt}
    </div>
  );
}

"use client";

import * as React from "react";
import { useState, useEffect } from "react";
import {
  ColumnDef,
  ColumnFiltersState,
  OnChangeFn,
  PaginationState,
  SortingState,
  VisibilityState,
  getCoreRowModel,
  getFacetedRowModel,
  getFacetedUniqueValues,
  getFilteredRowModel,
  getSortedRowModel,
  useReactTable,
} from "@tanstack/react-table";

import {
  ListTasksPageQueryResult,
  usePaginatedListTasks,
} from "@/queries/list-tasks";
import { TaskEntry } from "./data/schema";
import { DataTableBase, useRowSelectionSyncedToAtom } from "./data-table-base";

interface DataTableProps<TValue> {
  columns: ColumnDef<TaskEntry, TValue>[];
  query: ListTasksPageQueryResult;
  onPaginationChange: OnChangeFn<PaginationState>;
  pagination: PaginationState;

  // Customize this message to override what to display when there are no
  // results, such as if we get a React Query error.
  noResultsMessage?: string | React.ReactNode;
  isDataset?: boolean;
}

export function DataTable<TValue>({
  columns,
  query,
  pagination,
  onPaginationChange,
  noResultsMessage,
  isDataset,
}: DataTableProps<TValue>) {
  const data: TaskEntry[] = React.useMemo((): TaskEntry[] => {
    if (query.status === "success") {
      return query.data.tasks;
    }
    return [];
  }, [query]);

  const [rowSelection, setRowSelection] = useRowSelectionSyncedToAtom(data);

  const [columnVisibility, setColumnVisibility] =
    React.useState<VisibilityState>({});
  const [columnFilters, setColumnFilters] = React.useState<ColumnFiltersState>(
    [],
  );
  const [sorting, setSorting] = React.useState<SortingState>([]);

  const table = useReactTable({
    data,
    pageCount: -1,
    columns,
    state: {
      sorting,
      columnVisibility,
      rowSelection,
      columnFilters,
      pagination,
    },
    enableRowSelection: true,
    manualPagination: true,
    onRowSelectionChange: setRowSelection,
    onSortingChange: setSorting,
    onColumnFiltersChange: setColumnFilters,
    onColumnVisibilityChange: setColumnVisibility,
    getRowId: (row) => row.workflow_run_id,
    onPaginationChange: onPaginationChange,
    getCoreRowModel: getCoreRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFacetedRowModel: getFacetedRowModel(),
    getFacetedUniqueValues: getFacetedUniqueValues(),
  });

  if (query.status === "error") {
    return (
      <DataTableBase
        columns={columns}
        table={table}
        noResultsMessage="Error loading tasks."
        canGetNextPageOverride={false}
        loadingStatus={query.status}
        isDataset={isDataset}
      />
    );
  }

  const canGetNextPage =
    query.status === "success" && !!query.data.nextPageToken;

  return (
    <DataTableBase
      columns={columns}
      table={table}
      canGetNextPageOverride={canGetNextPage}
      noResultsMessage={noResultsMessage}
      loadingStatus={query.status}
      isDataset={isDataset}
    />
  );
}

export function useIndexPaginatedTasks(pageParams: {
  pageSize: number;
  pageIndex: number;
}): ListTasksPageQueryResult {
  // Start with empty string instead of undefined, because the default first
  // empty cursor is "" instead of undefined. If we don't find an exact match,
  // we accidentally end up with: [undefined, ""] for the first two elements in
  // our page cursor list.
  const [pageCursors, setPageCursors] = useState<Array<string | undefined>>([
    "",
  ]);

  useEffect(() => {
    setPageCursors([""]);
  }, []);

  if (pageParams.pageIndex >= pageCursors.length) {
    throw new Error("Page index out of bounds");
  }

  const cursor = pageCursors[pageParams.pageIndex];
  const query = usePaginatedListTasks({
    pageSize: pageParams.pageSize,
    pageCursor: cursor,
  });

  useEffect(() => {
    if (query.status === "success") {
      const nextToken = query.data.nextPageToken;
      setPageCursors((prevPageCursors) => {
        const lastToken = prevPageCursors[prevPageCursors.length - 1];
        if (nextToken !== lastToken) {
          return [...prevPageCursors, nextToken];
        } else {
          return prevPageCursors;
        }
      });
    }
  }, [query.status, query.data?.nextPageToken]);

  return query;
}

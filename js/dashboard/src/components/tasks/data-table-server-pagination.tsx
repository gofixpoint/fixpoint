"use client";

import * as React from "react";
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

import { ListTasksQueryResult } from "@/queries/list-tasks";
import { Task } from "./data/schema";
import { DataTableBase, useRowSelectionSyncedToAtom } from "./data-table-base";

interface DataTableProps<TValue> {
  columns: ColumnDef<Task, TValue>[];
  query: ListTasksQueryResult;
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
  let data: Task[] = React.useMemo((): Task[] => {
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
    getRowId: (row) => row.name,
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
      noResultsMessage={noResultsMessage}
      loadingStatus={query.status}
      isDataset={isDataset}
    />
  );
}
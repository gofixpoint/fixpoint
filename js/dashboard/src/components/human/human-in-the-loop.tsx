"use client";

import React, { useEffect, useState } from "react";
import { Metadata } from "next";
import { PaginationState } from "@tanstack/table-core";
import { Loader2 } from "lucide-react";
import { columns } from "@/components/tasks/columns";
import { DataTable } from "@/components/tasks/data-table-server-pagination";
import { usePaginatedListTasks } from "@/queries/list-tasks";

export default function HumanInTheLoop() {
  return <DataTableLoader />;
}

export const metadata: Metadata = {
  title: "Tasks",
  description: "A task and issue tracker build using Tanstack Table.",
};

const PAGE_SIZE = 50;

function DataTableLoader() {
  const [pageParams, setPageParams] = React.useState<PaginationState>({
    pageSize: PAGE_SIZE,
    pageIndex: 0,
  });

  const [pageCursors, setPageCursors] = useState<Array<string | undefined>>([
    "",
  ]);

  useEffect(() => {
    setPageCursors([""]);
  }, []);

  const cursor = pageCursors[pageParams.pageIndex];
  const listTasksQuery = usePaginatedListTasks({
    pageSize: pageParams.pageSize,
    pageCursor: cursor,
  });

  if (listTasksQuery.status === "error") {
    console.warn("Error fetching tasks");
    console.warn(listTasksQuery.error);
  }

  let noResultsMessage: string | React.ReactNode = (
    <>
      <p>No queued human tasks.</p>
    </>
  );
  // We use `isLoading` so that we don't redisplay the loading spinner when refetching
  if (listTasksQuery.isLoading) {
    noResultsMessage = (
      <>
        <p>Loading tasks...</p>

        <div className="flex items-center justify-center my-5">
          <Loader2 size={32} className="animate-spin" />
        </div>
      </>
    );
  }

  return (
    <div className="h-full">
      <DataTable
        query={listTasksQuery}
        columns={columns}
        pagination={pageParams}
        onPaginationChange={setPageParams}
        noResultsMessage={noResultsMessage}
      />
    </div>
  );
}

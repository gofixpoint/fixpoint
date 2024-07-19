"use client";

import React from "react";
import { Metadata } from "next";
import { useAtomValue } from "jotai";
import { PaginationState } from "@tanstack/table-core";
import { Loader2 } from "lucide-react";

import { envAtom } from "@/atoms/env";
import { columns } from "@/components/tasks/columns";
import { DataTable } from "@/components/tasks/data-table-server-pagination";
import {
  ListTasksQueryResult,
  useInfiniteListTasks,
} from "@/queries/list-tasks";

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
 

  const listTasksQuery = useInfiniteListTasks();

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
      <QueryStatus query={listTasksQuery} />
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

function QueryStatus(props: { query: ListTasksQueryResult }) {
  const { query } = props;
  const env = useAtomValue(envAtom);
  if (!env.flags.showListTasksQueryStatus) {
    return null;
  }

  const debugQueryStatusCSS = "border-x border-white px-4";
  return (
    <p>
      <span className={debugQueryStatusCSS}>
        Is loading: {query.isLoading ? "true" : "false"}
      </span>
      <span className={debugQueryStatusCSS}>
        Is fetching: {query.isFetching ? "true" : "false"}
      </span>
      <span className={debugQueryStatusCSS}>
        Is pending: {query.isPending ? "true" : "false"}
      </span>
    </p>
  );
}

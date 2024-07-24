"use client";

import { ColumnDef } from "@tanstack/react-table";
import { DateTime } from "luxon";
import { DataTableColumnHeader } from "@/components/ui/data-table-column-header";
import { Task, WorkflowStatus } from "./data/schema";
import { WorkflowStatusDisplay } from "./workflow-status";

export const columns: ColumnDef<Task>[] = [
  {
    accessorKey: "workflowId",
    meta: {
      displayName: "Workflow ID",
    },
    cell: ({ row }) => {
      return (
        <div className="flex flex-row w-[120px] justify-center">
          <span>{row.getValue<string>("workflowId")}</span>
        </div>
      );
    },
    header: ({ column }) => (
      <DataTableColumnHeader column={column} title="Workflow Id" />
    ),
  },
  {
    accessorKey: "workflowRunId",
    meta: {
      displayName: "Workflow Run ID",
    },
    cell: ({ row }) => {
      return (
        <div className="flex w-[120px] justify-center">
          <span>{row.getValue<string>("workflowRunId")}</span>
        </div>
      );
    },
    header: ({ column }) => (
      <DataTableColumnHeader column={column} title="Workflow Run Id" />
    ),
  },
  {
    accessorKey: "status",
    meta: {
      displayName: "Status",
    },
    cell: ({ row }) => {
      const status = row.getValue<string>("status");
      return (
        <div className="flex w-[120px]">
          <WorkflowStatusDisplay status={status as WorkflowStatus} />
        </div>
      );
    },
    header: ({ column }) => (
      <DataTableColumnHeader column={column} title="Status" />
    ),
  },
  {
    accessorKey: "createdAt",
    meta: {
      displayName: "Created At",
    },
    header: ({ column }) => (
      <DataTableColumnHeader column={column} title="Created At" />
    ),
    cell: ({ row }) => (
      <div className="min-w-[180px]">
        {DateTime.fromISO(
          row.getValue<Required<Task["createdAt"]>>("createdAt"),
        ).toFormat("yyyy-MM-dd  HH:mm:ss")}
      </div>
    ),
    enableSorting: true,
    enableHiding: true,
  },
];

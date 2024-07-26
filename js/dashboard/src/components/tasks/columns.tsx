"use client";

import { ColumnDef } from "@tanstack/react-table";
import { DateTime } from "luxon";
import { DataTableColumnHeader } from "@/components/ui/data-table-column-header";
import { TaskEntry, WorkflowStatus } from "./data/schema";
import { WorkflowStatusDisplay } from "./workflow-status";

export const columns: ColumnDef<TaskEntry>[] = [
  {
    accessorKey: "id",
    meta: {
      displayName: "ID",
    },
    cell: ({ row }) => {
      return (
        <div className="flex">
          <span>{row.getValue<string>("id")}</span>
        </div>
      );
    },
    header: ({ column }) => (
      <DataTableColumnHeader column={column} title="Id" />
    ),
  },
  {
    accessorKey: "task_id",
    meta: {
      displayName: "Task ID",
    },
    cell: ({ row }) => {
      return (
        <div className="flex">
          <span>{row.getValue<string>("task_id")}</span>
        </div>
      );
    },
    header: ({ column }) => (
      <DataTableColumnHeader column={column} title="Task Id" />
    ),
  },
  {
    accessorKey: "workflow_run_id",
    meta: {
      displayName: "Workflow Run ID",
    },
    cell: ({ row }) => {
      return (
        <div className="flex">
          <span>{row.getValue<string>("workflow_run_id")}</span>
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
    accessorKey: "created_at",
    meta: {
      displayName: "Created At",
    },
    header: ({ column }) => (
      <DataTableColumnHeader column={column} title="Created At" />
    ),
    cell: ({ row }) => (
      <div className="min-w-[180px]">
        {DateTime.fromISO(
          row.getValue<Required<TaskEntry["created_at"]>>("created_at"),
        ).toFormat("yyyy-MM-dd  HH:mm:ss")}
      </div>
    ),
    enableSorting: true,
    enableHiding: true,
  },
];

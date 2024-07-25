"use client";

import { ColumnDef } from "@tanstack/react-table";
import { DateTime } from "luxon";
import { DataTableColumnHeader } from "@/components/ui/data-table-column-header";
import { Task, WorkflowStatus } from "./data/schema";
import { WorkflowStatusDisplay } from "./workflow-status";

export const columns: ColumnDef<Task>[] = [
  {
    accessorKey: "id",
    meta: {
      displayName: "ID",
    },
    cell: ({ row }) => {
      return (
        <div className="flex flex-row w-[120px] justify-center">
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
        <div className="flex flex-row w-[120px] justify-center">
          <span>{row.getValue<string>("task_id")}</span>
        </div>
      );
    },
    header: ({ column }) => (
      <DataTableColumnHeader column={column} title="Task Id" />
    ),
  },
  {
    accessorKey: "source_node",
    meta: {
      displayName: "Source Node",
    },
    cell: ({ row }) => {
      return (
        <div className="flex flex-row w-[120px] justify-center">
          <span>{row.getValue<string>("source_node")}</span>
        </div>
      );
    },
    header: ({ column }) => (
      <DataTableColumnHeader column={column} title="Source Node" />
    ),
  },
  {
    accessorKey: "workflow_id",
    meta: {
      displayName: "Workflow ID",
    },
    cell: ({ row }) => {
      return (
        <div className="flex flex-row w-[120px] justify-center">
          <span>{row.getValue<string>("workflow_id")}</span>
        </div>
      );
    },
    header: ({ column }) => (
      <DataTableColumnHeader column={column} title="Workflow Id" />
    ),
  },
  {
    accessorKey: "workflow_run_id",
    meta: {
      displayName: "Workflow Run ID",
    },
    cell: ({ row }) => {
      return (
        <div className="flex w-[120px] justify-center">
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
          row.getValue<Required<Task["created_at"]>>("created_at"),
        ).toFormat("yyyy-MM-dd  HH:mm:ss")}
      </div>
    ),
    enableSorting: true,
    enableHiding: true,
  },
];

"use client";

import { ColumnDef } from "@tanstack/react-table";
import { DateTime } from "luxon";
import { DataTableColumnHeader } from "@/components/ui/data-table-column-header";
import { Task } from "./data/schema";


export const columns: ColumnDef<Task>[] = [

  {
    accessorKey: "createdAt",
    meta: {
      displayName: "Timestamp",
    },
    header: ({ column }) => (
      <DataTableColumnHeader column={column} title="Timestamp" />
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

"use client";

import React from "react";
import { flexRender, Row } from "@tanstack/react-table";

import { cn } from "@/lib/utils";
import { TaskEntry } from "@/components/tasks/data/schema";
import { TableCell, TableRow } from "@/components/ui/table";
import { UpDownTaskSidesheet } from "@/components/tasks/sidesheet";
import * as sheet from "@/components/ui/sheet";

interface TaskRowProps {
  allRows: Row<TaskEntry>[];
  rowIndex: number;
}

export function TaskRow(props: TaskRowProps) {
  const row = props.allRows[props.rowIndex];

  // TODO(dbmikus) we might want to have a higher-level atom or state that
  // allows us to only have one row open at a time
  const [open, setOpen] = React.useState(false);

  return (
    <sheet.Sheet open={open} onOpenChange={(open) => setOpen(open)}>
      {/* TODO(dylan) should this be a button? */}
      <TableRow
        data-state={row.getIsSelected() && "selected"}
        role="button"
        onClick={() => {
          setOpen(true);
        }}
      >
        <sheet.SheetTrigger asChild>
          <>
            {row.getVisibleCells().map((cell) => (
              <TableCell
                key={cell.id}
                className={cn(
                  // make sure left-most select column is aligned with header
                  cell.column.id === "select" ? "pl-4" : null,
                  cell.column.id === "timestamp" ? "w-40" : null,
                )}
              >
                {flexRender(cell.column.columnDef.cell, cell.getContext())}
              </TableCell>
            ))}
          </>
        </sheet.SheetTrigger>
      </TableRow>
      <UpDownTaskSidesheet
        open={open}
        setOpen={setOpen}
        rows={props.allRows}
        startingRowIndex={props.rowIndex}
      />
    </sheet.Sheet>
  );
}

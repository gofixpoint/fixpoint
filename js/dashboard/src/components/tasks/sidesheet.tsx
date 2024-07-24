import React from "react";
import { atom } from "jotai";
import { z } from "zod";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Row } from "@tanstack/react-table";
import * as VisuallyHidden from "@radix-ui/react-visually-hidden";
import { ArrowUp, ArrowDown, Maximize, Minimize } from "lucide-react";
import * as sheet from "@/components/ui/sheet";
import { Button } from "@/components/ui/button";
import {
  EntryField,
  Task,
  WorkflowStatus,
  workflowStatusEnum,
} from "@/components/tasks/data/schema";
import { H2, H3 } from "../ui/headings";
import { WorkflowStatusDisplay } from "./workflow-status";
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "../ui/form";
import { Input } from "../ui/input";
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectLabel,
  SelectTrigger,
  SelectValue,
} from "../ui/select";

type OnUpDownFn = (updown: "up" | "down") => void;

interface ControlSettings {
  upEnabled: boolean;
  downEnabled: boolean;
}

export interface TaskSidesheetProps {
  open: boolean;
  setOpen: React.Dispatch<React.SetStateAction<boolean>>;
  row: Task;
  onUpDownClick: OnUpDownFn;
  controlSettings: ControlSettings;
}

type AllowedSheetSizes = Extract<
  sheet.SheetContentProps["size"],
  "sm" | "full"
>;

const headerHeight = 48;

// You must nest this within a `sheet.Sheet` component.
export function TaskSidesheet(props: TaskSidesheetProps): React.JSX.Element {
  const [sheetSize, setSheetSize] = React.useState<AllowedSheetSizes>("sm");

  return (
    <sheet.SheetContent className="p-0" side="right" size={sheetSize}>
      <sheet.SheetHeader style={{ height: headerHeight }}>
        <VisuallyHidden.Root>
          <sheet.SheetTitle>LLM Log details</sheet.SheetTitle>
        </VisuallyHidden.Root>
        <ControlIcons
          sheetSize={sheetSize}
          setSheetSize={setSheetSize}
          onUpDownClick={props.onUpDownClick}
          controlSettings={props.controlSettings}
        />
      </sheet.SheetHeader>
      <SheetSections row={props.row} />
    </sheet.SheetContent>
  );
}

interface ControlIconsProps {
  sheetSize: sheet.SheetContentProps["size"];
  setSheetSize: React.Dispatch<React.SetStateAction<AllowedSheetSizes>>;
  onUpDownClick: OnUpDownFn;
  controlSettings: ControlSettings;
}

function ControlIcons(props: ControlIconsProps): React.JSX.Element {
  return (
    <div className="flex items-center space-x-1 my-0">
      <Button
        type="button"
        variant="ghost"
        size="icon"
        onClick={() => {
          if (props.sheetSize === "sm") {
            props.setSheetSize("full");
          } else {
            props.setSheetSize("sm");
          }
        }}
      >
        {props.sheetSize === "sm" ? <Maximize /> : <Minimize />}
      </Button>
      <Button
        type="button"
        variant="ghost"
        size="icon"
        disabled={!props.controlSettings.upEnabled}
        onClick={() => props.onUpDownClick("up")}
      >
        <ArrowUp />
      </Button>
      <Button
        type="button"
        variant="ghost"
        size="icon"
        disabled={!props.controlSettings.downEnabled}
        onClick={() => props.onUpDownClick("down")}
      >
        <ArrowDown />
      </Button>
    </div>
  );
}

interface SheetSectionsProps {
  row: Task;
}

function SheetSections(props: SheetSectionsProps): React.JSX.Element {
  return (
    <div
      className="px-6 pt-0 pb-6 overflow-y-auto gap-3 flex flex-col"
      style={{ maxHeight: `calc(100% - ${headerHeight}px)` }}
    >
      <H2>Task Details</H2>
      <div className="flex flex-col gap-2">
        <H3>Meta</H3>
        <div>
          <TaskSection name="Workflow Id" value={props.row.workflowId} />
          <TaskSection name="Workflow Run Id" value={props.row.workflowRunId} />
          <TaskSection
            name="Status"
            value={<WorkflowStatusDisplay status={props.row.status} />}
          />
          <TaskSection name="Created At" value={props.row.createdAt} />
        </div>
        <div></div>
        <H3>Task Fields</H3>
        <TaskEntriesForm
          entryFields={props.row.entryFields}
          status={props.row.status}
        />
      </div>
    </div>
  );
}

const formSchema = z.object({
  status: workflowStatusEnum,
  fields: z.record(z.string()),
});

function TaskEntriesForm(props: {
  entryFields: EntryField[];
  status: WorkflowStatus;
}): React.JSX.Element {
  const fieldValues = props.entryFields.reduce<{ [key: string]: any }>(
    (acc, ef) => {
      acc[ef.id] = ef.contents;
      return acc;
    },
    {},
  );
  // Define a submission form
  const form = useForm<z.infer<typeof formSchema>>({
    defaultValues: {
      fields: fieldValues,
      status: workflowStatusEnum.Enum.RUNNING,
    },
  });

  function onSubmit(values: z.infer<typeof formSchema>) {
    // Do something with the form values.
    console.log(values);
  }

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-8">
        {props.entryFields.map((ef) => {
          return (
            <FormField
              control={form.control}
              name={`fields.${ef.id}`}
              render={({ field }) => (
                <FormItem>
                  <FormLabel>{ef.display_name}</FormLabel>
                  <FormControl>
                    <Input {...field} />
                  </FormControl>
                  {ef.description && (
                    <FormDescription>{ef.description}</FormDescription>
                  )}
                  <FormMessage />
                </FormItem>
              )}
            />
          );
        })}
        {
          <FormField
            control={form.control}
            name="status"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Status</FormLabel>
                <FormControl>
                  <SelectStatus
                    status={field.value as WorkflowStatus}
                    onChange={field.onChange}
                    value={field.value as WorkflowStatus}
                  />
                </FormControl>
              </FormItem>
            )}
          />
        }
        <Button type="submit">Submit</Button>
      </form>
    </Form>
  );
}

function SelectStatus(props: {
  status: WorkflowStatus;
  onChange: (status: WorkflowStatus) => void;
  value: WorkflowStatus;
}): React.JSX.Element {
  return (
    <Select defaultValue={props.value} onValueChange={props.onChange}>
      <SelectTrigger className="w-[180px]">
        <SelectValue placeholder="Select a status" />
      </SelectTrigger>
      <SelectContent>
        <SelectGroup>
          {workflowStatusEnum.options.map((status) => {
            return <SelectItem value={status}>{status}</SelectItem>;
          })}
        </SelectGroup>
      </SelectContent>
    </Select>
  );
}

interface TaskSectionProps {
  name: string;
  value: string | JSX.Element;
}

function TaskSection(props: TaskSectionProps): React.JSX.Element {
  return (
    <div className="flex flex-row">
      <div className="text-left font-semibold min-w-[200px]">{props.name}</div>
      <div className="text-left min-w-[300px] flex flex-row items-center">
        <span>{props.value}</span>
      </div>
    </div>
  );
}

export interface UpDownTaskSidesheetProps {
  open: boolean;
  setOpen: React.Dispatch<React.SetStateAction<boolean>>;
  rows: Row<Task>[];
  startingRowIndex: number;
}

// The LLMLogSidesheet but hooked up so that we can navigate between llm log
// rows.
export function UpDownLLMLogSidesheet(
  props: UpDownTaskSidesheetProps,
): React.JSX.Element {
  // When we close the sheet, we want to unmount it so that its inner state can
  // be reset on the next mount.
  if (!props.open) {
    return <></>;
  }
  return <InnerUpDownTaskSidesheet {...props} />;
}

function InnerUpDownTaskSidesheet(
  props: UpDownTaskSidesheetProps,
): React.JSX.Element {
  const [index, setIndex] = React.useState(props.startingRowIndex);
  const row = props.rows[index];

  const onUpDownClick = (updown: "up" | "down") => {
    if (updown === "up" && index > 0) {
      setIndex(index - 1);
    } else if (updown === "down" && index < props.rows.length - 1) {
      setIndex(index + 1);
    }
  };

  return (
    <TaskSidesheet
      {...props}
      row={row.original}
      onUpDownClick={onUpDownClick}
      controlSettings={{
        upEnabled: index > 0,
        downEnabled: index < props.rows.length - 1,
      }}
    />
  );
}

interface ISectionsOpen {
  attributes: boolean;
  messages: boolean;
  evaluations: boolean;
  datasets: boolean;
  applicationLogs: boolean;
}

const sectionsOpenBaseAtom = atom<ISectionsOpen>({
  attributes: true,
  messages: true,
  evaluations: true,
  datasets: true,
  applicationLogs: true,
});

const sectionsOpenAtom = atom(
  (get) => get(sectionsOpenBaseAtom),
  (_get, set, update: string[]) => {
    set(sectionsOpenBaseAtom, {
      attributes: update.includes("attributes"),
      messages: update.includes("messages"),
      evaluations: update.includes("evaluations"),
      datasets: update.includes("datasets"),
      applicationLogs: update.includes("app-logs"),
    });
  },
);

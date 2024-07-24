import React from "react";
import { z } from "zod";
import { useForm } from "react-hook-form";
import { Row } from "@tanstack/react-table";
import * as VisuallyHidden from "@radix-ui/react-visually-hidden";
import {
  ArrowUp,
  ArrowDown,
  Maximize,
  Minimize,
  Bot,
  CircleUserRound,
} from "lucide-react";
import * as sheet from "@/components/ui/sheet";
import { Button } from "@/components/ui/button";
import {
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
  SelectTrigger,
  SelectValue,
} from "../ui/select";
import { useUpdateTask } from "@/queries/update-task";
import { Textarea } from "../ui/textarea";

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
        <H3>Attributes</H3>
        <div>
          <TaskSection name="Task Id" value={props.row.id} />
          <TaskSection name="Source Node" value={props.row.source_node} />
          <TaskSection name="Workflow Id" value={props.row.workflow_id} />
          <TaskSection
            name="Workflow Run Id"
            value={props.row.workflow_run_id}
          />
          <TaskSection
            name="Status"
            value={<WorkflowStatusDisplay status={props.row.status} />}
          />
          <TaskSection name="Created At" value={props.row.created_at} />
        </div>
        <div></div>
        <H3>Task Fields</H3>
        <TaskEntriesForm task={props.row} />
      </div>
    </div>
  );
}

const formSchema = z.object({
  status: workflowStatusEnum,
  fields: z.record(z.string()),
});

function TaskEntriesForm(props: { task: Task }): React.JSX.Element {
  const { mutate: updateTask } = useUpdateTask();
  // Define a submission form
  const form = useForm<z.infer<typeof formSchema>>({
    defaultValues: {
      status: workflowStatusEnum.Enum.RUNNING,
    },
  });

  function onSubmit(values: z.infer<typeof formSchema>) {
    // Do something with the form values.
    let updatedTask = {
      ...props.task,
      status: values.status,
      entry_fields: props.task.entry_fields.map((ef) => {
        if (values.fields[ef.id]) {
          let editable_config = { ...ef.editable_config };
          editable_config.human_contents = values.fields[ef.id];
          return { ...ef, editable_config };
        }
        return ef;
      }),
    };
    updateTask(updatedTask);
  }

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-8">
        {props.task.entry_fields.map((ef) => {
          const defaultHumanContents = ef.editable_config.human_contents
            ? ef.editable_config.human_contents
            : ef.contents;
          return (
            <FormField
              control={form.control}
              name={`fields.${ef.id}`}
              render={({ field }) => (
                <FormItem className="bg-gray-100 bg-opacity-10 rounded-md p-4">
                  <FormLabel>{ef.display_name}</FormLabel>
                  {ef.description && (
                    <FormDescription>{ef.description}</FormDescription>
                  )}
                  <FormControl>
                    <>
                      <div className="flex gap-2 items-center">
                        <Bot />
                        <Textarea disabled={true} value={ef.contents} />
                      </div>
                      {ef.editable_config.is_editable && (
                        <div className="flex gap-2 items-center">
                          <CircleUserRound />
                          <Input
                            {...field}
                            defaultValue={defaultHumanContents}
                          />
                        </div>
                      )}
                    </>
                  </FormControl>
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
        <Button type="submit">Update</Button>
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
export function UpDownTaskSidesheet(
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

import { z } from "zod";
import { isSet } from "@/lib/utils";
import { metadata } from "@/app/layout";

export enum FineTuneStatus {
  UNSPECIFIED = "FINE_TUNE_STATUS_UNSPECIFIED",
  VALIDATING_FILES = "FINE_TUNE_STATUS_VALIDATING_FILES",
  QUEUED = "FINE_TUNE_STATUS_QUEUED",
  RUNNING = "FINE_TUNE_STATUS_RUNNING",
  SUCCEEDED = "FINE_TUNE_STATUS_SUCCEEDED",
  FAILED = "FINE_TUNE_STATUS_FAILED",
  CANCELLED = "FINE_TUNE_STATUS_CANCELLED",
}

export const workflowStatusEnum = z.enum([
  "RUNNING",
  "SUSPENDED",
  "FAILED",
  "CANCELLED",
  "COMPLETED",
  "TERMINATED",
  "TIMED_OUT",
  "CONTINUED_AS_NEW",
]);

const editableConfigSchema = z.object({
  is_editable: z.boolean(),
  is_required: z.boolean(),
  human_contents: z.string().nullable(),
});

const entryFieldSchema = z.object({
  id: z.string(),
  display_name: z.string().nullable(),
  description: z.string().nullable(),
  contents: z.any().nullable(),
  editable_config: editableConfigSchema,
});

const taskEntrySchema = z.object({
  id: z.string(),
  task_id: z.string(),
  workflow_id: z.string(),
  workflow_run_id: z.string(),
  status: workflowStatusEnum,
  created_at: z.string(),
  updated_at: z.string(),
  entry_fields: z.array(entryFieldSchema),
  metadata: z.record(z.string()).nullable(),
  source_node: z.string().nullable(),
});

export const tasksResponseSchema = z.array(taskEntrySchema);

export type WorkflowStatus = z.infer<typeof workflowStatusEnum>;
export type Task = z.infer<typeof taskEntrySchema>;
export const listTasksRequestSchema = z.object({});
export const listTasksResponseSchema = z.object({
  tasks: z.array(taskEntrySchema),
  nextPageToken: z.string().optional(),
  totalEntries: z
    .union([z.string(), z.number(), z.null(), z.undefined()])
    .transform((arg, ctx) => {
      if (!isSet(arg)) {
        return null;
      }
      try {
        return BigInt(arg);
      } catch (e) {
        console.error("Failed to parse totalEntries as BigInt");
        console.error(e);
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          message: `Failed to parse totalEntries as BigInt: ${arg}`,
        });
        return z.NEVER;
      }
    })
    .refine((arg) => {
      if (arg === null) {
        return true;
      }
      return arg >= 0;
    }),
});
export type EntryField = z.infer<typeof entryFieldSchema>;
export type ListTasksRequest = z.infer<typeof listTasksRequestSchema>;
export type ListTasksResponse = z.infer<typeof listTasksResponseSchema>;
export type ListTasksResponseParsed = z.infer<typeof listTasksResponseSchema>;

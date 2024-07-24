import { z } from "zod";


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
    "CONTINUED_AS_NEW"
])

const editableConfigSchema = z.object({
    is_editable: z.boolean(),
    is_required: z.boolean(),
    human_contents: z.boolean(),
})

const entryFieldSchema = z.object({
    id: z.string(),
    display_name: z.string(),
    description: z.string().optional(),
    contents: z.string().optional(),
    editable_config: editableConfigSchema
})

const taskSchema = z.object({
    workflowId: z.string(),
    workflowRunId: z.string(),
    status: workflowStatusEnum,
    createdAt: z.string(),
    updatedAt: z.string(),
    entryFields: z.array(entryFieldSchema)
})
export type WorkflowStatus = z.infer<typeof workflowStatusEnum>;
export type Task = z.infer<typeof taskSchema>;
export const listDatasetsRequestSchema = z.object({});
export const listDatasetsResponseSchema = z.object({
    tasks: z.array(taskSchema),
  });
export type EntryField = z.infer<typeof entryFieldSchema>;
export type ListDatasetsRequest = z.infer<typeof listDatasetsRequestSchema>;
export type ListDatasetsResponse = z.infer<typeof listDatasetsResponseSchema>;
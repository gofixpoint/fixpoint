import { z } from "zod";

const taskSchema = z.object({
    id: z.string(),
    createdAt: z.string(),
    updatedAt: z.string(),
    name: z.string(),
    description: z.string(),
    status: z.string(),
})
export type Task = z.infer<typeof taskSchema>;

export const listDatasetsRequestSchema = z.object({});
export const listDatasetsResponseSchema = z.object({
    tasks: z.array(taskSchema),
  });
export type ListDatasetsRequest = z.infer<typeof listDatasetsRequestSchema>;
export type ListDatasetsResponse = z.infer<typeof listDatasetsResponseSchema>;
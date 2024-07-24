"use server";

import { Task } from "@/components/tasks/data/schema";
import { createClient } from "@/utils/supabase/server";

export async function fetchTasksAction() {
  const supabase = createClient();
  const { data: tasks } = await supabase.from("workflow_tasks").select();
  return tasks;
}

export async function updateTaskAction(task: Task): Promise<Task> {
  const supabase = createClient();

  const { error } = await supabase.from("workflow_tasks").upsert(task);
  if (error) throw error;

  return task;
}

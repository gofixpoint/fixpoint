"use server";

import { TaskEntry } from "@/components/tasks/data/schema";
import { createClient } from "@/utils/supabase/server";

export async function fetchTasksAction() {
  const supabase = createClient();
  const { data: tasks } = await supabase.from("task_entries").select();
  return tasks;
}

export async function updateTaskAction(task: TaskEntry): Promise<TaskEntry> {
  const supabase = createClient();

  const { error } = await supabase.from("task_entries").upsert(task);
  if (error) throw error;

  return task;
}

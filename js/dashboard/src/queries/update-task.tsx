import { useMutation, useQueryClient } from "@tanstack/react-query";
import { updateTaskAction } from "@/utils/supabase/actions";
import { ListTasksResponseParsed, Task } from "@/components/tasks/data/schema";
import { useToast } from "@/components/ui/use-toast";

export function useUpdateTask() {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  const mutation = useMutation({
    mutationFn: (task: Task) => {
      return updateTaskAction(task);
    },
    onSuccess: (updatedTask: Task) => {
      // On success update the query to include the new dataset in the query
      queryClient.setQueryData(
        ["tasks"],
        (oldData: ListTasksResponseParsed) => {
          // Change if tasks are not the same

          // Replace old tasks with updated one (dedup on id)
          const updatedTasks = oldData.tasks.map((task) =>
            task.id === updatedTask.id ? updatedTask : task,
          );

          const ret = {
            tasks: updatedTasks,
          };

          return ret;
        },
      );

      toast({
        title: "Task updated",
        description: `Task ${updatedTask.id} has been updated`,
      });
    },
  });

  return mutation;
}

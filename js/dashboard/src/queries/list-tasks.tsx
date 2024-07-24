import {
  UseQueryResult,
  DefaultError,
  InfiniteData,
  useQuery,
  QueryKey,
} from "@tanstack/react-query";
import {
  ListTasksResponseParsed,
  tasksResponseSchema,
} from "@/components/tasks/data/schema";
import { fetchTasksAction } from "@/utils/supabase/actions";

export type ListTasksPages = InfiniteData<ListTasksResponseParsed>;

export type ListTasksQueryResult = UseQueryResult<ListTasksPages, DefaultError>;

export type ListTasksPageQueryResult = UseQueryResult<
  ListTasksResponseParsed,
  DefaultError
>;

export type PageParams = { pageSize: number; pageCursor?: string };

async function fetchTasks(
  pageParams: PageParams,
): Promise<ListTasksResponseParsed> {
  const tasks = await fetchTasksAction();
  const parsedTasks = tasksResponseSchema.parse(tasks);

  return {
    tasks: parsedTasks,
    totalEntries: BigInt(parsedTasks.length),
  };
}

export function usePaginatedListTasks(
  pageParams: PageParams,
): ListTasksPageQueryResult {
  const query = useQuery<
    ListTasksResponseParsed,
    DefaultError,
    ListTasksResponseParsed,
    QueryKey
  >({
    queryKey: formatQueryKey(pageParams),
    queryFn: async () => {
      return fetchTasks(pageParams);
    },
  });

  return query;
}

function formatQueryKey(pageParams: PageParams): QueryKey {
  return ["tasks"];
}

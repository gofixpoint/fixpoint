import {
  UseQueryResult,
  DefaultError,
  InfiniteData,
  useQuery,
  QueryKey,
} from "@tanstack/react-query";
import { ListTasksResponseParsed } from "@/components/tasks/data/schema";

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
  //TODO: Implement
  return {
    tasks: [],
    totalEntries: BigInt(10),
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
  return ["tasks", pageParams.pageSize, pageParams.pageCursor];
}

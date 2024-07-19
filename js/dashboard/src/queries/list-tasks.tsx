import {
  useInfiniteQuery,
  UseInfiniteQueryResult,
  UseQueryResult,
  DefaultError,
  InfiniteData,
} from "@tanstack/react-query";
import {
    listDatasetsResponseSchema,
    ListDatasetsResponse
} from "@/components/tasks/data/schema";

type PageParam = string | undefined;

export type ListTasksPages = InfiniteData<ListDatasetsResponse>;

export type ListTasksQueryResult = UseInfiniteQueryResult<
  ListTasksPages,
  DefaultError
>;

type InfQueryKey = ["inf-tasks"];

export function useInfiniteListTasks(
): ListTasksQueryResult {
  const infQuery = useInfiniteQuery<
    ListDatasetsResponse,
    DefaultError,
    ListTasksPages,
    InfQueryKey,
    PageParam
  >({
    // TODO fix
    queryKey: formatInfQueryKey(),
    queryFn: async ({ pageParam }) => fetchTasks(),
    initialPageParam: undefined,
    getNextPageParam: (lastPage) => lastPage?.nextPageToken,
  });

  return infQuery;
}

function formatInfQueryKey(): InfQueryKey {
  return ["inf-tasks"];
}

export type ListTasksPageQueryResult = UseQueryResult<
   ListDatasetsResponse,
  DefaultError
>;

export type PageParams = { pageSize: number; pageCursor?: string };


function parseResponse(resp: unknown): ListDatasetsResponse {
  return listDatasetsResponseSchema.parse(resp);
}

async function fetchTasks(): Promise<ListDatasetsResponse> {
    //TODO: Implement
    return {
        tasks: []
    }
}

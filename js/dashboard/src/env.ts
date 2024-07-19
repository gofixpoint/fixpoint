import { cache } from "react";

export type Env = {
  flags: Flags;
};

export interface Flags {
    showListTasksQueryStatus: boolean
}

// Cache this so that server-side components can re-use the cache value. Right
// now we force all Next.js pages to be dynamic, but later we can let Next.js be
// smart about static versus dynamic rendering based on cached values.
export const loadEnv = cache((): Env => {
  const env: Env = {
    flags: {
        showListTasksQueryStatus: isEnvTrue("SHOW_LIST_TASKS_QUERY_STATUS"),
    },
  };
  return env;
});

const isEnvTrue = (varname: string): boolean => {
    const val = process.env[varname];
    if (val === undefined) {
      return false;
    }
    return ["true", "1", "yes", "on"].includes(val.toLowerCase());
  };
import { cache } from "react";

export type Env = {
  flags: Flags;
};

export interface Flags {

}

// Cache this so that server-side components can re-use the cache value. Right
// now we force all Next.js pages to be dynamic, but later we can let Next.js be
// smart about static versus dynamic rendering based on cached values.
export const loadEnv = cache((): Env => {
  const env: Env = {
    flags: {
    },
  };
  return env;
});

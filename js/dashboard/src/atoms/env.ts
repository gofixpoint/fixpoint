import { useSetAtom } from "jotai";
import { atomRequired } from "@/atoms/utils";
import { Env } from "@/env";

export const envAtom = atomRequired<Env>();

export const useLoadEnvIntoAtom = (env: Env): void => {
  const setEnvAtom = useSetAtom(envAtom);
  setEnvAtom(env);
};

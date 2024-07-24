"use client";

import React from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Provider as JotaiProvider } from "jotai";
import { Env } from "@/env";
import { useLoadEnvIntoAtom } from "@/atoms/env";
import { TooltipProvider } from "@/components/ui/tooltip";

const queryClient = new QueryClient();

export function RootProvider(props: {
  children: React.ReactNode;
  env: Env;
}): React.JSX.Element {
  return (
    <JotaiProvider>
      <QueryClientProvider client={queryClient}>
        <TooltipProvider>
          <AtomsInit env={props.env}>{props.children}</AtomsInit>
        </TooltipProvider>
      </QueryClientProvider>
    </JotaiProvider>
  );
}

function AtomsInit(props: { children: React.ReactNode; env: Env }) {
  useLoadEnvIntoAtom(props.env);

  return <>{props.children}</>;
}

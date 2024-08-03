"use client";

import React from "react";
import { AuthProvider } from "@propelauth/nextjs/client";
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
          <AuthProvider authUrl={props.env.flags.next_public_auth_url}>
            <AtomsInit env={props.env}>{props.children}</AtomsInit>
          </AuthProvider>
        </TooltipProvider>
      </QueryClientProvider>
    </JotaiProvider>
  );
}

function AtomsInit(props: { children: React.ReactNode; env: Env }) {
  useLoadEnvIntoAtom(props.env);

  return <>{props.children}</>;
}

import React from "react";

import { cn } from "@/lib/utils";

export function H1(props: { children: React.ReactNode }) {
  return (
    <h1 className="text-3xl font-bold tracking-tight text-primary">
      {props.children}
    </h1>
  );
}

export function H2(props: { children: React.ReactNode }) {
  return (
    <h2 className="text-2xl font-bold tracking-tight text-primary">
      {props.children}
    </h2>
  );
}
export function H3(props: { children: React.ReactNode; className?: string }) {
  return (
    <h3 className={cn("text-xl tracking-tight text-primary", props.className)}>
      {props.children}
    </h3>
  );
}

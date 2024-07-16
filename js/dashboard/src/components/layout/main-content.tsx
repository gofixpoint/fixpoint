import React from "react";
import { cva, type VariantProps } from "class-variance-authority";

import { H2, H3 } from "@/components/ui/headings";
import { CrumbItemProps, BreadCrumbs } from "@/components/ui/breadcrumbs";

const mainContentVariants = cva("h-screen flex-1 flex-col space-y-8 md:flex", {
  variants: {
    variant: {
      default: "p-8",
      withSidePanel: "pt-8 pl-8 pb-0 pr-0",
    },
  },
  defaultVariants: {
    variant: "default",
  },
});

export interface MainContentProps
  extends VariantProps<typeof mainContentVariants> {
  children: React.ReactNode;
  title: string;
  subTitle?: string;
  description?: string;
  breadCrumbItems?: CrumbItemProps[];
}

export function MainContent(props: MainContentProps): JSX.Element {
  return (
    <main className={mainContentVariants({ variant: props.variant })}>
      <div className="flex items-center justify-between space-y-2">
        <div className="h-full">
          {props.breadCrumbItems && (
            <BreadCrumbs className="mb-4" crumbItems={props.breadCrumbItems} />
          )}
          <H2>{props.title}</H2>
          {props.subTitle && <H3>{props.subTitle}</H3>}
          {props.description && <p className="mt-2">{props.description}</p>}
        </div>
      </div>
      {props.children}
    </main>
  );
}

/**
 * Use this as a wrapper for your main content within a ResizablePanel if you
 * are using the `withSidePanel` variant.
 */
export function SidePanelMain(props: {
  children: React.ReactNode;
}): JSX.Element {
  return (
    <div className="overflow-auto max-h-full pb-8 pr-8">{props.children}</div>
  );
}

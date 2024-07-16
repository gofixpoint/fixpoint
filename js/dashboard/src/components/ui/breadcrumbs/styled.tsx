"use client";

import { cn } from "@/lib/utils";
import * as headless from "./headless";

export interface BreadcrumbsProps {
  crumbItems: headless.CrumbItemProps[];
  className?: string;
}

export const BreadCrumbs: React.FC<BreadcrumbsProps> = ({
  crumbItems,
  className,
}: BreadcrumbsProps) => {
  return (
    <headless.BreadCrumbs
      crumbAs={CrumbItem}
      dividerAs={Divider}
      className={cn("flex flex-row space-x-3 text-sm", className)}
      crumbItems={crumbItems}
    />
  );
};

export type CrumbItemProps = Pick<
  headless.CrumbItemProps,
  "href" | "text" | "selected"
>;

const CrumbItem: React.FC<headless.CrumbItemProps> = (props) => {
  return (
    <headless.CrumbItem
      className={cn(
        props.href && "hover:underline hover:text-accent-foreground",
        props.selected ? "text-accent-foreground" : "text-muted-foreground",
      )}
      {...props}
    />
  );
};

const Divider = () => {
  return <headless.CrumbDivider className="text-muted-foreground" />;
};

"use client";

import React from "react";
import Link from "next/link";

import * as routing from "@/lib/routing";
import { injectSeparatorsDynamic } from "@/lib/collections";

interface BreadcrumbsContextArgs {}

const BreadcrumbsContext = React.createContext<BreadcrumbsContextArgs>({});

export interface BreadcrumbsProps {
  crumbItems: CrumbItemProps[];
  crumbAs?: React.FC<CrumbItemProps>;
  dividerAs?: React.FC<CrumbDividerProps>;
  style?: React.CSSProperties;
  className?: string;
}

export const BreadCrumbs: React.FC<BreadcrumbsProps> = (
  props: BreadcrumbsProps,
) => {
  const CrumbItemAs = props.crumbAs || CrumbItem;
  const DividerAs = props.dividerAs || CrumbDivider;
  const crumbItems = props.crumbItems.map((crumb, index) => (
    <CrumbItemAs key={crumb.href || `no-href-${index}`} {...crumb} />
  ));
  const crumbComponents = injectSeparatorsDynamic(
    crumbItems,
    (_elem: unknown, index: number) => <DividerAs key={`divider-${index}`} />,
  );

  return (
    <BreadcrumbsContext.Provider value={{}}>
      <span className={props.className} style={props.style}>
        {crumbComponents}
      </span>
    </BreadcrumbsContext.Provider>
  );
};

export interface CrumbItemProps extends routing.breadcrumbs.BreadCrumb {
  style?: React.CSSProperties;
  className?: string;
}

export const CrumbItem: React.FC<CrumbItemProps> = (props) => {
  const inner = props.href ? (
    <Link href={props.href}>{props.text}</Link>
  ) : (
    props.text
  );
  return (
    <span className={props.className} style={props.style}>
      {inner}
    </span>
  );
};

export interface CrumbDividerProps {
  style?: React.CSSProperties;
  className?: string;
}

export const CrumbDivider: React.FC<CrumbDividerProps> = (
  props: CrumbDividerProps,
) => {
  return <span {...props}>/</span>;
};

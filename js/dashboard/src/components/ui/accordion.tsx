"use client";

import * as React from "react";
import * as AccordionPrimitive from "@radix-ui/react-accordion";
import { ChevronDown, ChevronRight } from "lucide-react";
import { cva, type VariantProps } from "class-variance-authority";

import { cn } from "@/lib/utils";

const Accordion = AccordionPrimitive.Root;

const accordionItemVariants = cva("", {
  variants: {
    divider: {
      thin: "border-b",
      // we use both padding and margin to equally space the border
      fat: "border-b-2 pb-9 mb-9",
    },
  },
  defaultVariants: {
    divider: "thin",
  },
});

interface AccordionItemProps
  extends React.ComponentPropsWithoutRef<typeof AccordionPrimitive.Item>,
    VariantProps<typeof accordionItemVariants> {}

const AccordionItem = React.forwardRef<
  React.ElementRef<typeof AccordionPrimitive.Item>,
  AccordionItemProps
>(({ className, divider, ...props }, ref) => (
  <AccordionPrimitive.Item
    ref={ref}
    className={cn(accordionItemVariants({ divider }), className)}
    {...props}
  />
));
AccordionItem.displayName = "AccordionItem";

const defaultVariant = "rightflip";

const accordionTriggerVariants = cva(
  "flex flex-1 items-center py-4 font-medium transition-all hover:underline",
  {
    variants: {
      variant: {
        rightflip: "justify-between [&[data-state=open]>svg]:rotate-180",
        left90: "justify-start [&[data-state=open]>svg]:rotate-90",
      },
    },
    defaultVariants: {
      variant: defaultVariant,
    },
  },
);

interface AccordionTriggerProps
  extends React.ComponentPropsWithoutRef<typeof AccordionPrimitive.Trigger>,
    VariantProps<typeof accordionTriggerVariants> {}

const AccordionTrigger = React.forwardRef<
  React.ElementRef<typeof AccordionPrimitive.Trigger>,
  AccordionTriggerProps
>(({ className, children, variant, ...props }, ref) => {
  const chevronClassName = "h-4 w-4 shrink-0 transition-transform duration-200";

  return (
    <AccordionPrimitive.Header className="flex">
      <AccordionPrimitive.Trigger
        ref={ref}
        className={cn(accordionTriggerVariants({ variant }), className)}
        {...props}
      >
        {variant === "left90" && <ChevronRight className={chevronClassName} />}
        <span className={cn(variant === "left90" && "ml-2")}>{children}</span>
        {variant === "rightflip" && (
          <ChevronDown className={chevronClassName} />
        )}
      </AccordionPrimitive.Trigger>
    </AccordionPrimitive.Header>
  );
});
AccordionTrigger.displayName = AccordionPrimitive.Trigger.displayName;

interface AccordionContentProps
  extends React.ComponentPropsWithoutRef<typeof AccordionPrimitive.Content> {
  variant?: "rightflip" | "left90" | null;
}

const AccordionContent = React.forwardRef<
  React.ElementRef<typeof AccordionPrimitive.Content>,
  AccordionContentProps
>(({ className, children, variant, ...props }, ref) => {
  variant = variant || defaultVariant;

  return (
    <AccordionPrimitive.Content
      ref={ref}
      className="overflow-hidden text-sm transition-all data-[state=closed]:animate-accordion-up data-[state=open]:animate-accordion-down"
      {...props}
    >
      <div
        className={cn("pb-4 pt-0", variant === "left90" && "ml-6", className)}
      >
        {children}
      </div>
    </AccordionPrimitive.Content>
  );
});

AccordionContent.displayName = AccordionPrimitive.Content.displayName;

export { Accordion, AccordionItem, AccordionTrigger, AccordionContent };
export type { AccordionTriggerProps };

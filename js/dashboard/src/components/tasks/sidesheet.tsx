import React from "react";
import { atom, useAtom, useAtomValue } from "jotai";
import { Row } from "@tanstack/react-table";
import * as VisuallyHidden from "@radix-ui/react-visually-hidden";
import { ArrowUp, ArrowDown, Maximize, Minimize } from "lucide-react";

import { envAtom } from "@/atoms/env";
import * as sheet from "@/components/ui/sheet";
import { Button } from "@/components/ui/button";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { Task } from "@/components/tasks/data/schema";

type OnUpDownFn = (updown: "up" | "down") => void;

interface ControlSettings {
  upEnabled: boolean;
  downEnabled: boolean;
}

export interface LLMLogSidesheetProps {
  open: boolean;
  setOpen: React.Dispatch<React.SetStateAction<boolean>>;
  row: Task;
  onUpDownClick: OnUpDownFn;
  controlSettings: ControlSettings;
}

type AllowedSheetSizes = Extract<
  sheet.SheetContentProps["size"],
  "sm" | "full"
>;

const headerHeight = 48;

// You must nest this within a `sheet.Sheet` component.
export function LLMLogSidesheet(
  props: LLMLogSidesheetProps,
): React.JSX.Element {
  const [sheetSize, setSheetSize] = React.useState<AllowedSheetSizes>("sm");

  return (
    <sheet.SheetContent className="p-0" side="right" size={sheetSize}>
      <sheet.SheetHeader style={{ height: headerHeight }}>
        <VisuallyHidden.Root>
          <sheet.SheetTitle>LLM Log details</sheet.SheetTitle>
        </VisuallyHidden.Root>
        <ControlIcons
          sheetSize={sheetSize}
          setSheetSize={setSheetSize}
          onUpDownClick={props.onUpDownClick}
          controlSettings={props.controlSettings}
        />
      </sheet.SheetHeader>
      <SheetSections row={props.row} />
    </sheet.SheetContent>
  );
}

interface ControlIconsProps {
  sheetSize: sheet.SheetContentProps["size"];
  setSheetSize: React.Dispatch<React.SetStateAction<AllowedSheetSizes>>;
  onUpDownClick: OnUpDownFn;
  controlSettings: ControlSettings;
}

function ControlIcons(props: ControlIconsProps): React.JSX.Element {
  return (
    <div className="flex items-center space-x-1 my-0">
      <Button
        type="button"
        variant="ghost"
        size="icon"
        onClick={() => {
          if (props.sheetSize === "sm") {
            props.setSheetSize("full");
          } else {
            props.setSheetSize("sm");
          }
        }}
      >
        {props.sheetSize === "sm" ? <Maximize /> : <Minimize />}
      </Button>
      <Button
        type="button"
        variant="ghost"
        size="icon"
        disabled={!props.controlSettings.upEnabled}
        onClick={() => props.onUpDownClick("up")}
      >
        <ArrowUp />
      </Button>
      <Button
        type="button"
        variant="ghost"
        size="icon"
        disabled={!props.controlSettings.downEnabled}
        onClick={() => props.onUpDownClick("down")}
      >
        <ArrowDown />
      </Button>
    </div>
  );
}

interface SheetSectionsProps {
  row: Task;
}

function SheetSections(props: SheetSectionsProps): React.JSX.Element {
  const [openSections, setOpenSections] = useAtom(sectionsOpenAtom);
  const env = useAtomValue(envAtom);

  return (
    <div
      className="px-6 pt-0 pb-6 overflow-y-auto"
      style={{ maxHeight: `calc(100% - ${headerHeight}px)` }}
    >
      <Accordion
        className="w-full grid gap-4"
        type="multiple"
        value={sectionsToValuesStr(openSections)}
        onValueChange={setOpenSections}
      >
        <AccordionItem value="details">
          <MyAccordionTrigger>Task details</MyAccordionTrigger>
          <AccordionContent>
            <div>More content...</div>
          </AccordionContent>
        </AccordionItem>
      </Accordion>
    </div>
  );
}

function MyAccordionTrigger(props: {
  children: React.ReactNode;
}): React.JSX.Element {
  return (
    <AccordionTrigger className="text-lg" variant="rightflip">
      {props.children}
    </AccordionTrigger>
  );
}

export interface UpDownLLMLogSidesheetProps {
  open: boolean;
  setOpen: React.Dispatch<React.SetStateAction<boolean>>;
  rows: Row<Task>[];
  startingRowIndex: number;
}

// The LLMLogSidesheet but hooked up so that we can navigate between llm log
// rows.
export function UpDownLLMLogSidesheet(
  props: UpDownLLMLogSidesheetProps,
): React.JSX.Element {
  // When we close the sheet, we want to unmount it so that its inner state can
  // be reset on the next mount.
  if (!props.open) {
    return <></>;
  }
  return <InnerUpDownLLMLogSidesheet {...props} />;
}

function InnerUpDownLLMLogSidesheet(
  props: UpDownLLMLogSidesheetProps,
): React.JSX.Element {
  const [index, setIndex] = React.useState(props.startingRowIndex);
  const row = props.rows[index];

  const onUpDownClick = (updown: "up" | "down") => {
    if (updown === "up" && index > 0) {
      setIndex(index - 1);
    } else if (updown === "down" && index < props.rows.length - 1) {
      setIndex(index + 1);
    }
  };

  return (
    <LLMLogSidesheet
      {...props}
      row={row.original}
      onUpDownClick={onUpDownClick}
      controlSettings={{
        upEnabled: index > 0,
        downEnabled: index < props.rows.length - 1,
      }}
    />
  );
}

interface ISectionsOpen {
  attributes: boolean;
  messages: boolean;
  evaluations: boolean;
  datasets: boolean;
  applicationLogs: boolean;
}

const sectionsOpenBaseAtom = atom<ISectionsOpen>({
  attributes: true,
  messages: true,
  evaluations: true,
  datasets: true,
  applicationLogs: true,
});

const sectionsOpenAtom = atom(
  (get) => get(sectionsOpenBaseAtom),
  (_get, set, update: string[]) => {
    set(sectionsOpenBaseAtom, {
      attributes: update.includes("attributes"),
      messages: update.includes("messages"),
      evaluations: update.includes("evaluations"),
      datasets: update.includes("datasets"),
      applicationLogs: update.includes("app-logs"),
    });
  },
);

const sectionsToValuesStr = (sections: ISectionsOpen): string[] => {
  return [
    sections.attributes ? "attributes" : "",
    sections.messages ? "messages" : "",
    sections.evaluations ? "evaluations" : "",
    sections.datasets ? "datasets" : "",
    sections.applicationLogs ? "app-logs" : "",
  ].filter((s) => s !== "");
};

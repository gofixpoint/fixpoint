import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function darkCN(classes: string | string[]) {
  if (typeof classes === "string") {
    classes = classes.split(" ");
  }
  return cn(...classes, ...classes.map((c) => `dark:${c}`));
}

export function isSet<T>(value: T | null | undefined): value is T {
  return value !== null && value !== undefined;
}

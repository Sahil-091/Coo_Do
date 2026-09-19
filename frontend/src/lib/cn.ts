import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

/** Merge Tailwind class lists safely (later conflicting classes win). */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

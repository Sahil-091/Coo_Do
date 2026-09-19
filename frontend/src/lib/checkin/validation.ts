import { z } from "zod";
import { FEELINGS, NEEDS } from "./types";

export const checkInSchema = z.object({
  feelings: z.array(z.enum(FEELINGS)).min(1, "Select at least one feeling."),
  statedNeed: z.enum(NEEDS),
  timeOfDay: z.enum(["morning", "afternoon", "evening", "night"]),
});

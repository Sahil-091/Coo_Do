import { z } from "zod";

// Mirrors app/schemas.py's MIN_PASSWORD_LENGTH on the core-api side —
// keep these in sync if either changes. Client-side validation is UX
// only; the backend re-validates independently regardless.
export const MIN_PASSWORD_LENGTH = 8;

export const registerSchema = z.object({
  email: z.email("Enter a valid email address."),
  password: z
    .string()
    .min(MIN_PASSWORD_LENGTH, `Use at least ${MIN_PASSWORD_LENGTH} characters.`),
});

export const loginSchema = z.object({
  email: z.email("Enter a valid email address."),
  password: z.string().min(1, "Enter your password."),
});

export const ageVerificationSchema = z.object({
  dateOfBirth: z
    .string()
    .min(1, "Enter your date of birth.")
    .refine((value) => !Number.isNaN(Date.parse(value)), "Enter a valid date.")
    .refine((value) => new Date(value) <= new Date(), "Date of birth can't be in the future."),
});

export const displayNameSchema = z.object({
  displayName: z.string().max(60, "Keep it under 60 characters.").optional(),
});

export const consentTypeSchema = z.enum([
  "ai_chat",
  "anonymous_community",
  "matching_visibility",
  "institutional_data_sharing",
]);

export type ConsentType = z.infer<typeof consentTypeSchema>;

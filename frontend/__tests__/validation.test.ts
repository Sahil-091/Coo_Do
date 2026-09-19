import { describe, expect, test } from "vitest";
import {
  ageVerificationSchema,
  displayNameSchema,
  loginSchema,
  MIN_PASSWORD_LENGTH,
  registerSchema,
} from "../src/lib/auth/validation";

describe("registerSchema", () => {
  test("accepts a valid email and password", () => {
    const result = registerSchema.safeParse({
      email: "student@example.com",
      password: "correct-horse-battery-staple",
    });
    expect(result.success).toBe(true);
  });

  test("rejects an invalid email", () => {
    const result = registerSchema.safeParse({ email: "not-an-email", password: "longenough1" });
    expect(result.success).toBe(false);
  });

  test(`rejects a password shorter than ${MIN_PASSWORD_LENGTH} characters`, () => {
    const result = registerSchema.safeParse({
      email: "student@example.com",
      password: "short1",
    });
    expect(result.success).toBe(false);
  });
});

describe("loginSchema", () => {
  test("rejects an empty password", () => {
    const result = loginSchema.safeParse({ email: "student@example.com", password: "" });
    expect(result.success).toBe(false);
  });
});

describe("ageVerificationSchema", () => {
  test("accepts a past date", () => {
    const result = ageVerificationSchema.safeParse({ dateOfBirth: "2000-01-01" });
    expect(result.success).toBe(true);
  });

  test("rejects a future date", () => {
    const future = new Date();
    future.setFullYear(future.getFullYear() + 1);
    const result = ageVerificationSchema.safeParse({
      dateOfBirth: future.toISOString().slice(0, 10),
    });
    expect(result.success).toBe(false);
  });

  test("rejects an empty value", () => {
    const result = ageVerificationSchema.safeParse({ dateOfBirth: "" });
    expect(result.success).toBe(false);
  });

  test("rejects an unparseable date string", () => {
    const result = ageVerificationSchema.safeParse({ dateOfBirth: "not-a-date" });
    expect(result.success).toBe(false);
  });
});

describe("displayNameSchema", () => {
  test("optional field accepts being omitted", () => {
    const result = displayNameSchema.safeParse({});
    expect(result.success).toBe(true);
  });

  test("rejects a name over 60 characters", () => {
    const result = displayNameSchema.safeParse({ displayName: "x".repeat(61) });
    expect(result.success).toBe(false);
  });
});

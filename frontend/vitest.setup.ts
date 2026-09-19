import "@testing-library/jest-dom/vitest";
import { afterEach, expect } from "vitest";
import { cleanup } from "@testing-library/react";
import { toHaveNoViolations } from "jest-axe";

// Server Components import the server-only environment schema. These values
// exist solely in Vitest's process; real dev and production boot still fail
// closed when their required secrets are absent.
process.env.SESSION_SECRET ??= "test-session-secret-that-is-long-enough-32";
process.env.INTERNAL_SHARED_SECRET ??= "test-internal-shared-secret";

expect.extend(toHaveNoViolations);

// Testing Library doesn't auto-cleanup under Vitest the way it does under
// Jest's global afterEach detection — without this, DOM (including
// AdaptivePanel's portaled content) leaks across tests in the same file.
afterEach(() => {
  cleanup();
});

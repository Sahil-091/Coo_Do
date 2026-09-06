import "@testing-library/jest-dom/vitest";
import { afterEach, expect } from "vitest";
import { cleanup } from "@testing-library/react";
import { toHaveNoViolations } from "jest-axe";

expect.extend(toHaveNoViolations);

// Testing Library doesn't auto-cleanup under Vitest the way it does under
// Jest's global afterEach detection — without this, DOM (including
// AdaptivePanel's portaled content) leaks across tests in the same file.
afterEach(() => {
  cleanup();
});

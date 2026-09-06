import { expect, test } from "vitest";
import { render, screen } from "@testing-library/react";
import { axe } from "jest-axe";
import Page from "../src/app/(app)/page";

test("home page renders a welcome heading and shortcut links", () => {
  render(<Page />);
  expect(screen.getByRole("heading", { level: 1, name: /welcome back/i })).toBeInTheDocument();
  expect(screen.getByRole("link", { name: /check in/i })).toHaveAttribute("href", "/checkin");
  expect(screen.getByRole("link", { name: /tiny action/i })).toHaveAttribute("href", "/tiny-action");
  expect(screen.getByRole("link", { name: /journal/i })).toHaveAttribute("href", "/journal");
});

test("home page has no axe accessibility violations", async () => {
  const { container } = render(<Page />);
  expect(await axe(container)).toHaveNoViolations();
});

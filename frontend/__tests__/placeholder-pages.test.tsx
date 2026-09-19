import { render, screen } from "@testing-library/react";
import { axe } from "jest-axe";
import { describe, expect, test, vi } from "vitest";

vi.mock("server-only", () => ({}));
vi.mock("@/lib/auth/dal", () => ({
  requireOnboardedUser: vi.fn(),
}));
vi.mock("@/safety/resources.server", () => ({
  getCrisisResources: vi.fn().mockResolvedValue({
    region: "India",
    emergency_note: "If you may be in immediate danger, call local emergency services.",
    resources: [
      {
        name: "Tele-MANAS",
        phone: "14416",
        phone_uri: "tel:14416",
        description: "24/7 mental-health support",
      },
    ],
  }),
}));
vi.mock("@/lib/core-api-server", () => ({
  internalApiFetch: vi.fn().mockResolvedValue([
    {
      id: "resource-1", category: "Immediate support", title: "Tele-MANAS",
      summary: "A national support helpline.", contact_label: "Call", contact_value: "14416",
      contact_uri: "tel:14416", booking_steps: ["Call when you are ready."],
      what_to_expect: "You can begin with what feels easiest to say.",
      opening_lines: ["I would like to talk to someone."], last_verified_at: "2026-09-19",
    },
  ]),
}));

import CommunityPage from "../src/app/(app)/community/page";
import ProfessionalHelpPage from "../src/app/(app)/professional-help/page";
import SafetyPage from "../src/app/(app)/safety/page";

// Settings (Phase 2), Check-in (Phase 3), Tiny Action (Phase 4), Journal
// (Phase 8), and Professional Help (Phase 7) are real data-fetching pages.
// Professional Help uses the core-api mock above; the other pages' more
// specific dependencies need dedicated tests.
const pages = [
  ["Community", CommunityPage],
  ["Safety", SafetyPage],
] as const;

describe.each(pages)("%s placeholder page", (_name, PageComponent) => {
  test("renders exactly one h1 and no axe violations", async () => {
    const page = await PageComponent();
    const { container } = render(page);
    expect(screen.getAllByRole("heading", { level: 1 })).toHaveLength(1);
    expect(await axe(container)).toHaveNoViolations();
  });
});

test("Professional Help displays curated directory content without a check-in", async () => {
  const page = await ProfessionalHelpPage();
  const { container } = render(page);
  expect(screen.getByRole("heading", { level: 1, name: /real support/i })).toBeInTheDocument();
  expect(screen.getByText("Tele-MANAS")).toBeInTheDocument();
  expect(screen.getByRole("link", { name: /need immediate support/i })).toHaveAttribute("href", "/safety");
  expect(await axe(container)).toHaveNoViolations();
});

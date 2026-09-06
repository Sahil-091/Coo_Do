import { render, screen } from "@testing-library/react";
import { axe } from "jest-axe";
import { describe, expect, test } from "vitest";

import JournalPage from "../src/app/(app)/journal/page";
import CommunityPage from "../src/app/(app)/community/page";
import ProfessionalHelpPage from "../src/app/(app)/professional-help/page";
import SafetyPage from "../src/app/(app)/safety/page";

// Settings (Phase 2), Check-in (Phase 3), and Tiny Action (Phase 4) are
// no longer placeholders — they're real data-fetching/interactive pages
// whose dependencies need proper mocking (server-only-guarded modules
// aren't split the way Next's real bundler splits "use server"
// boundaries under plain Vite/Vitest). See settings-page.test.tsx,
// checkin-flow.test.tsx, and tiny-action-flow.test.tsx.
const pages = [
  ["Journal", JournalPage],
  ["Community", CommunityPage],
  ["Professional Help", ProfessionalHelpPage],
  ["Safety", SafetyPage],
] as const;

describe.each(pages)("%s placeholder page", (_name, PageComponent) => {
  test("renders exactly one h1 and no axe violations", async () => {
    const { container } = render(<PageComponent />);
    expect(screen.getAllByRole("heading", { level: 1 })).toHaveLength(1);
    expect(await axe(container)).toHaveNoViolations();
  });
});

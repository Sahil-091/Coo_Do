import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, test, vi } from "vitest";

const internalApiFetch = vi.fn();

vi.mock("@/lib/auth/dal", () => ({
  requireOnboardedUser: vi.fn(async () => ({ userId: "student-1" })),
}));

vi.mock("@/lib/core-api-server", () => ({ internalApiFetch }));

// The page test exercises the student-visible state. The server actions are
// covered by core-api integration tests, so avoid importing their server-only
// dependencies into jsdom here.
vi.mock("../src/app/(app)/journal/actions", () => ({
  createJournalEntryAction: vi.fn(),
  deleteJournalEntryAction: vi.fn(),
  deleteAllJournalEntriesAction: vi.fn(),
  exportJournalAction: vi.fn(),
}));

describe("Journal page", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  test("shows private entries, separate indicators, and real export/delete controls", async () => {
    internalApiFetch.mockImplementation((path: string) => {
      if (path.endsWith("/journal/comparisons")) {
        return Promise.resolve([
          { window_days: 7, narrative: "You made a reflection in this period." },
          { window_days: 30, narrative: "There are no reflections from the last 30 days yet." },
          { window_days: 90, narrative: "There are no reflections from the last 90 days yet." },
        ]);
      }
      if (path.endsWith("/real-life-indicators")) {
        return Promise.resolve([
          { key: "tiny_actions", sentence: "Tiny actions completed: 2." },
          { key: "help_seeking", sentence: "Help-seeking actions taken: 1." },
        ]);
      }
      if (path.endsWith("/journal")) {
        return Promise.resolve([
          {
            id: "entry-1", body: "I wrote a private reflection.",
            created_at: "2026-09-19T08:00:00Z", updated_at: "2026-09-19T08:00:00Z",
          },
        ]);
      }
      throw new Error(`Unexpected path: ${path}`);
    });

    const { default: JournalPage } = await import("../src/app/(app)/journal/page");
    render(await JournalPage());

    expect(screen.getByText("I wrote a private reflection.")).toBeInTheDocument();
    expect(screen.getByText("Tiny actions completed: 2.")).toBeInTheDocument();
    expect(screen.getByText("Help-seeking actions taken: 1.")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /export journal/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /delete all reflections/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /delete reflection/i })).toBeInTheDocument();
  });

  test("has a safe unavailable state and does not imply a save or deletion occurred", async () => {
    internalApiFetch.mockRejectedValue(new Error("core-api unavailable"));

    const { default: JournalPage } = await import("../src/app/(app)/journal/page");
    render(await JournalPage());

    expect(screen.getByRole("alert")).toHaveTextContent(
      /temporarily unavailable\. nothing was saved or deleted/i,
    );
  });
});

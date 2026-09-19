import { render, screen } from "@testing-library/react";
import { describe, expect, test, vi } from "vitest";

vi.mock("@/app/(app)/community/local/actions", () => ({
  clearActivityAreaAction: vi.fn(async () => ({})),
  createMeetupAction: vi.fn(async () => ({ error: "not used" })),
  rsvpMeetupAction: vi.fn(async () => ({ error: "not used" })),
  setActivityAreaAction: vi.fn(async () => ({})),
}));

describe("LocalMeetupsClient", () => {
  test("renders only server-provided public venues and aggregate RSVP information", async () => {
    const { LocalMeetupsClient } = await import("@/app/(app)/community/local/LocalMeetupsClient");
    render(
      <LocalMeetupsClient
        venues={[{ id: "venue-1", name: "Central Library", category: "library", map_url: "https://maps.example/library" }]}
        initialMeetups={[{
          id: "meetup-1",
          title: "Calm study group",
          description: "Bring notes and work alongside others.",
          category: "study_group",
          venue_name: "Central Library",
          venue_map_url: "https://maps.example/library",
          starts_at: "2026-10-01T10:00:00Z",
          max_participants: 8,
          joining_count: 2,
          maybe_count: 1,
          my_rsvp: null,
        }]}
      />
    );

    expect(screen.getByRole("option", { name: "Central Library" })).toHaveValue("venue-1");
    expect(screen.getByRole("link", { name: /central library/i })).toHaveAttribute(
      "href",
      "https://maps.example/library"
    );
    expect(screen.getByText(/2 joining.*1 maybe.*maximum 8/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Join" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Maybe" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Ignore" })).toBeInTheDocument();
  });
});

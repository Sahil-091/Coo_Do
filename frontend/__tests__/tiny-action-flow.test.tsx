import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { axe } from "jest-axe";
import { beforeEach, describe, expect, test, vi } from "vitest";
import { TinyActionFlow } from "../src/app/(app)/tiny-action/TinyActionFlow";
import type { TinyActionRung } from "../src/lib/tiny-action/types";

const logAttemptAction = vi.fn();
const getSuggestionAction = vi.fn();

vi.mock("@/lib/tiny-action/actions", () => ({
  logAttemptAction: (...args: unknown[]) => logAttemptAction(...args),
  getSuggestionAction: (...args: unknown[]) => getSuggestionAction(...args),
}));

const LADDER: TinyActionRung[] = [
  { id: "rung-1", difficultyLevel: 1, title: "Step outside for 2 minutes", description: "Just do it." },
  { id: "rung-2", difficultyLevel: 2, title: "Go where people are", description: "Head somewhere." },
  { id: "rung-3", difficultyLevel: 3, title: "Message one classmate", description: "Send a message." },
];

describe("TinyActionFlow", () => {
  beforeEach(() => {
    logAttemptAction.mockReset();
    getSuggestionAction.mockReset();
    logAttemptAction.mockResolvedValue({ showSupportNudge: false });
  });

  test("starts on the middle (difficulty 2) rung by default", () => {
    render(<TinyActionFlow initialLadder={LADDER} />);
    expect(screen.getByRole("heading", { name: "Go where people are" })).toBeInTheDocument();
  });

  test("Make it bigger and Make it smaller navigate the ladder client-side, no logging", () => {
    render(<TinyActionFlow initialLadder={LADDER} />);

    fireEvent.click(screen.getByRole("button", { name: /make it bigger/i }));
    expect(screen.getByRole("heading", { name: "Message one classmate" })).toBeInTheDocument();
    expect(logAttemptAction).not.toHaveBeenCalled();

    // At the ceiling now — "make it bigger" should be gone.
    expect(screen.queryByRole("button", { name: /make it bigger/i })).not.toBeInTheDocument();
  });

  test("Make it smaller (above the floor) logs 'reduced' and moves down without ending the flow", async () => {
    render(<TinyActionFlow initialLadder={LADDER} />);
    fireEvent.click(screen.getByRole("button", { name: /^make it smaller$/i }));

    await waitFor(() => expect(logAttemptAction).toHaveBeenCalledWith("rung-2", "reduced", undefined));
    expect(await screen.findByRole("heading", { name: "Step outside for 2 minutes" })).toBeInTheDocument();
  });

  test("at the floor, the button relabels and still logs 'reduced'", async () => {
    render(<TinyActionFlow initialLadder={LADDER} />);
    fireEvent.click(screen.getByRole("button", { name: /^make it smaller$/i })); // -> rung 1 (floor)
    await screen.findByRole("heading", { name: "Step outside for 2 minutes" });

    expect(screen.queryByRole("button", { name: /^make it smaller$/i })).not.toBeInTheDocument();
    const floorButton = screen.getByRole("button", { name: /even this feels like too much/i });
    fireEvent.click(floorButton);

    await waitFor(() =>
      expect(logAttemptAction).toHaveBeenLastCalledWith("rung-1", "reduced", undefined)
    );
    expect(await screen.findByText(/real information, not a failure/i, {}, { timeout: 3000 })).toBeInTheDocument();
  });

  test("floor acknowledgment shows the support nudge only when the backend says to", async () => {
    logAttemptAction.mockResolvedValue({ showSupportNudge: true });
    render(<TinyActionFlow initialLadder={LADDER} />);
    fireEvent.click(screen.getByRole("button", { name: /^make it smaller$/i }));
    await screen.findByRole("heading", { name: "Step outside for 2 minutes" });
    fireEvent.click(screen.getByRole("button", { name: /even this feels like too much/i }));

    const link = await screen.findByRole("link", { name: /see how to get support/i });
    expect(link).toHaveAttribute("href", "/professional-help");
  });

  test("floor acknowledgment does NOT show the nudge card when the backend says not to", async () => {
    logAttemptAction.mockResolvedValue({ showSupportNudge: false });
    render(<TinyActionFlow initialLadder={LADDER} />);
    fireEvent.click(screen.getByRole("button", { name: /^make it smaller$/i }));
    await screen.findByRole("heading", { name: "Step outside for 2 minutes" });
    fireEvent.click(screen.getByRole("button", { name: /even this feels like too much/i }));

    await screen.findByText(/real information, not a failure/i, {}, { timeout: 3000 });
    expect(screen.queryByRole("link", { name: /see how to get support/i })).not.toBeInTheDocument();
  });

  test("Complete logs 'completed' for the currently shown rung and shows the completed view", async () => {
    render(<TinyActionFlow initialLadder={LADDER} />);
    fireEvent.click(screen.getByRole("button", { name: /make it bigger/i })); // move to rung 3 first
    fireEvent.click(screen.getByRole("button", { name: /i did it/i }));

    await waitFor(() => expect(logAttemptAction).toHaveBeenCalledWith("rung-3", "completed", undefined));
    expect(await screen.findByText(/you did that\. that counts\./i)).toBeInTheDocument();
  });

  test("Skip logs 'skipped' and shows a non-judgmental skipped view", async () => {
    render(<TinyActionFlow initialLadder={LADDER} />);
    fireEvent.click(screen.getByRole("button", { name: /not right now/i }));

    await waitFor(() => expect(logAttemptAction).toHaveBeenCalledWith("rung-2", "skipped", undefined));
    expect(await screen.findByText(/that’s okay/i)).toBeInTheDocument();
  });

  test("passes checkinId through to every logged attempt when provided", async () => {
    render(<TinyActionFlow initialLadder={LADDER} checkinId="checkin-abc" />);
    fireEvent.click(screen.getByRole("button", { name: /i did it/i }));
    await waitFor(() =>
      expect(logAttemptAction).toHaveBeenCalledWith("rung-2", "completed", "checkin-abc")
    );
  });

  test("'See another' fetches a fresh ladder and resets to its middle rung", async () => {
    const newLadder: TinyActionRung[] = [
      { id: "new-1", difficultyLevel: 1, title: "Roll your shoulders", description: "Ten seconds." },
      { id: "new-2", difficultyLevel: 2, title: "Stretch a few minutes", description: "Right where you are." },
      { id: "new-3", difficultyLevel: 3, title: "Move for 10 minutes", description: "Anything physical." },
    ];
    getSuggestionAction.mockResolvedValue({ ladder: newLadder, suggestedAttemptId: "attempt-x" });

    render(<TinyActionFlow initialLadder={LADDER} />);
    fireEvent.click(screen.getByRole("button", { name: /not right now/i }));
    await screen.findByText(/that’s okay/i);

    fireEvent.click(screen.getByRole("button", { name: /see another/i }));
    expect(await screen.findByRole("heading", { name: "Stretch a few minutes" })).toBeInTheDocument();
  });

  test("shows an error message and lets the student keep trying if logging fails", async () => {
    logAttemptAction.mockResolvedValue({ error: "Couldn't save that. Please try again." });
    render(<TinyActionFlow initialLadder={LADDER} />);
    fireEvent.click(screen.getByRole("button", { name: /i did it/i }));

    expect(await screen.findByRole("alert")).toHaveTextContent(/couldn't save that/i);
    // Should stay on the ladder view, not silently advance to "completed".
    expect(screen.getByRole("heading", { name: "Go where people are" })).toBeInTheDocument();
  });

  test("has no axe violations on the ladder view", async () => {
    const { container } = render(<TinyActionFlow initialLadder={LADDER} />);
    expect(await axe(container)).toHaveNoViolations();
  });

  test(
    "has no axe violations on the floor + support-nudge view",
    async () => {
      logAttemptAction.mockResolvedValue({ showSupportNudge: true });
      const { container } = render(<TinyActionFlow initialLadder={LADDER} />);
      fireEvent.click(screen.getByRole("button", { name: /^make it smaller$/i }));
      await screen.findByRole("heading", { name: "Step outside for 2 minutes" });
      fireEvent.click(screen.getByRole("button", { name: /even this feels like too much/i }));
      // Two async round-trips plus an axe-core DOM scan in one test —
      // measurably CPU-heavy (observed 2.3s-5.3s even in isolation).
      // Under full-suite parallel load this occasionally exceeded a
      // 3000ms wait; both the wait and the test's own timeout are
      // extended here rather than masking it with a blanket global bump.
      await screen.findByText(/real information, not a failure/i, {}, { timeout: 8000 });
      expect(await axe(container)).toHaveNoViolations();
    },
    15000
  );
});

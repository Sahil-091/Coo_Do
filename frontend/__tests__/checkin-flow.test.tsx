import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { axe } from "jest-axe";
import { beforeEach, describe, expect, test, vi } from "vitest";
import { CheckInFlow } from "../src/app/(app)/checkin/CheckInFlow";

const submitCheckInAction = vi.fn();

vi.mock("@/lib/checkin/actions", () => ({
  submitCheckInAction: (...args: unknown[]) => submitCheckInAction(...args),
}));

describe("CheckInFlow", () => {
  beforeEach(() => {
    submitCheckInAction.mockReset();
    submitCheckInAction.mockResolvedValue({
      result: { path: "tiny_action", reason: "A small step might help right now.", checkinId: "test-checkin-id" },
    });
  });

  test("Continue is disabled until at least one feeling is selected", () => {
    render(<CheckInFlow />);
    expect(screen.getByRole("button", { name: /continue/i })).toBeDisabled();

    fireEvent.click(screen.getByRole("checkbox", { name: "Lonely" }));
    expect(screen.getByRole("button", { name: /continue/i })).not.toBeDisabled();
  });

  test("all 10 feeling options and all 8 need options render", () => {
    render(<CheckInFlow />);
    expect(screen.getAllByRole("checkbox")).toHaveLength(10);

    fireEvent.click(screen.getByRole("checkbox", { name: "Lonely" }));
    fireEvent.click(screen.getByRole("button", { name: /continue/i }));

    expect(screen.getAllByRole("radio")).toHaveLength(8);
  });

  test("need selection behaves as a true single-select (radio) group", () => {
    render(<CheckInFlow />);
    fireEvent.click(screen.getByRole("checkbox", { name: "Lonely" }));
    fireEvent.click(screen.getByRole("button", { name: /continue/i }));

    fireEvent.click(screen.getByRole("radio", { name: "Relax" }));
    fireEvent.click(screen.getByRole("radio", { name: "Study" }));

    expect(screen.getByRole("radio", { name: "Relax" })).not.toBeChecked();
    expect(screen.getByRole("radio", { name: "Study" })).toBeChecked();
  });

  test("Back returns to the feelings step with prior selections preserved", () => {
    render(<CheckInFlow />);
    fireEvent.click(screen.getByRole("checkbox", { name: "Lonely" }));
    fireEvent.click(screen.getByRole("checkbox", { name: "Exhausted" }));
    fireEvent.click(screen.getByRole("button", { name: /continue/i }));

    fireEvent.click(screen.getByRole("button", { name: /^back$/i }));

    expect(screen.getByRole("checkbox", { name: "Lonely" })).toBeChecked();
    expect(screen.getByRole("checkbox", { name: "Exhausted" })).toBeChecked();
  });

  test("submitting calls the action with selected feelings, need, and a computed time-of-day, then shows the result", async () => {
    render(<CheckInFlow />);
    fireEvent.click(screen.getByRole("checkbox", { name: "Lonely" }));
    fireEvent.click(screen.getByRole("button", { name: /continue/i }));
    fireEvent.click(screen.getByRole("radio", { name: "Relax" }));
    fireEvent.click(screen.getByRole("button", { name: /see what might help/i }));

    await waitFor(() => expect(submitCheckInAction).toHaveBeenCalledTimes(1));

    const [, formData] = submitCheckInAction.mock.calls[0] as [unknown, FormData];
    expect(formData.getAll("feelings")).toEqual(["lonely"]);
    expect(formData.get("statedNeed")).toBe("relax");
    expect(["morning", "afternoon", "evening", "night"]).toContain(formData.get("timeOfDay"));

    expect(await screen.findByText(/a small step might help right now/i)).toBeInTheDocument();
  });

  test("result step links to the correct destination for the returned path", async () => {
    submitCheckInAction.mockResolvedValue({
      result: { path: "professional_help", reason: "Here's how to ask for help.", checkinId: "test-checkin-id" },
    });
    render(<CheckInFlow />);
    fireEvent.click(screen.getByRole("checkbox", { name: "Sad" }));
    fireEvent.click(screen.getByRole("button", { name: /continue/i }));
    fireEvent.click(screen.getByRole("radio", { name: "Ask for help" }));
    fireEvent.click(screen.getByRole("button", { name: /see what might help/i }));

    const link = await screen.findByRole("link", { name: /see how to get help/i });
    // professional_help doesn't have an attempt-tracking concept yet —
    // no checkinId param should be appended here.
    expect(link).toHaveAttribute("href", "/professional-help");
  });

  test("tiny_action links carry the checkinId through as a query param", async () => {
    submitCheckInAction.mockResolvedValue({
      result: { path: "tiny_action", reason: "One small step.", checkinId: "abc-123-real-id" },
    });
    render(<CheckInFlow />);
    fireEvent.click(screen.getByRole("checkbox", { name: "Exhausted" }));
    fireEvent.click(screen.getByRole("button", { name: /continue/i }));
    fireEvent.click(screen.getByRole("radio", { name: "Relax" }));
    fireEvent.click(screen.getByRole("button", { name: /see what might help/i }));

    const link = await screen.findByRole("link", { name: /see your tiny action/i });
    expect(link).toHaveAttribute("href", "/tiny-action?checkinId=abc-123-real-id");
  });

  test("shows an error state and lets the student retry if the action fails", async () => {
    submitCheckInAction.mockResolvedValue({ error: "Something went wrong saving your check-in. Please try again." });
    render(<CheckInFlow />);
    fireEvent.click(screen.getByRole("checkbox", { name: "Angry" }));
    fireEvent.click(screen.getByRole("button", { name: /continue/i }));
    fireEvent.click(screen.getByRole("radio", { name: "Relax" }));
    fireEvent.click(screen.getByRole("button", { name: /see what might help/i }));

    expect(await screen.findByRole("alert")).toHaveTextContent(/something went wrong/i);
    expect(screen.getByRole("button", { name: /try again/i })).toBeInTheDocument();
  });

  test("has no axe violations on the feelings step", async () => {
    const { container } = render(<CheckInFlow />);
    expect(await axe(container)).toHaveNoViolations();
  });

  test("has no axe violations on the need step", async () => {
    const { container } = render(<CheckInFlow />);
    fireEvent.click(screen.getByRole("checkbox", { name: "Confused" }));
    fireEvent.click(screen.getByRole("button", { name: /continue/i }));
    expect(await axe(container)).toHaveNoViolations();
  });

  test("has no axe violations on the result step", async () => {
    const { container } = render(<CheckInFlow />);
    fireEvent.click(screen.getByRole("checkbox", { name: "Empty" }));
    fireEvent.click(screen.getByRole("button", { name: /continue/i }));
    fireEvent.click(screen.getByRole("radio", { name: "Relax" }));
    fireEvent.click(screen.getByRole("button", { name: /see what might help/i }));
    await screen.findByText(/a small step might help right now/i);
    expect(await axe(container)).toHaveNoViolations();
  });
});

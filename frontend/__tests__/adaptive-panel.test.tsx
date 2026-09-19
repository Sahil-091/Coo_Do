import { fireEvent, render, screen } from "@testing-library/react";
import { axe } from "jest-axe";
import { useState } from "react";
import { expect, test, vi } from "vitest";
import { AdaptivePanel } from "../src/components/ui/AdaptivePanel";

function Harness() {
  const [open, setOpen] = useState(false);
  return (
    <div>
      <button onClick={() => setOpen(true)}>Open panel</button>
      <AdaptivePanel open={open} onClose={() => setOpen(false)} title="Test panel">
        <p>Panel body content</p>
      </AdaptivePanel>
    </div>
  );
}

test("AdaptivePanel: renders nothing when closed", () => {
  render(
    <AdaptivePanel open={false} onClose={vi.fn()} title="Hidden">
      <p>Body</p>
    </AdaptivePanel>
  );
  expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
});

test("AdaptivePanel: has correct dialog semantics and no axe violations when open", async () => {
  const { container } = render(
    <AdaptivePanel open onClose={vi.fn()} title="Accessible panel">
      <p>Body</p>
    </AdaptivePanel>
  );

  const dialog = screen.getByRole("dialog", { name: /accessible panel/i });
  expect(dialog).toHaveAttribute("aria-modal", "true");

  expect(await axe(container)).toHaveNoViolations();
});

test("AdaptivePanel: Escape key calls onClose", () => {
  const onClose = vi.fn();
  render(
    <AdaptivePanel open onClose={onClose} title="Panel">
      <p>Body</p>
    </AdaptivePanel>
  );
  fireEvent.keyDown(document, { key: "Escape" });
  expect(onClose).toHaveBeenCalledTimes(1);
});

test("AdaptivePanel: clicking the backdrop calls onClose", () => {
  const onClose = vi.fn();
  const { container } = render(
    <AdaptivePanel open onClose={onClose} title="Panel">
      <p>Body</p>
    </AdaptivePanel>
  );
  const backdrop = container.parentElement?.querySelector('[aria-hidden="true"]');
  expect(backdrop).toBeTruthy();
  if (backdrop) fireEvent.click(backdrop);
  expect(onClose).toHaveBeenCalledTimes(1);
});

test("AdaptivePanel: focus returns to the trigger element after closing", async () => {
  render(<Harness />);
  const trigger = screen.getByRole("button", { name: /open panel/i });

  trigger.focus();
  expect(trigger).toHaveFocus();

  fireEvent.click(trigger);
  const dialog = await screen.findByRole("dialog");
  expect(dialog).toHaveFocus();

  fireEvent.keyDown(document, { key: "Escape" });
  expect(trigger).toHaveFocus();
});

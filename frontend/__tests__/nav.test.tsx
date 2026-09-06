import { fireEvent, render, screen, within } from "@testing-library/react";
import { axe } from "jest-axe";
import { expect, test, vi } from "vitest";
import { DesktopSidebar } from "../src/components/AppShell/DesktopSidebar";
import { MobileTabBar } from "../src/components/AppShell/MobileTabBar";

vi.mock("next/navigation", () => ({
  usePathname: () => "/checkin",
}));

test("DesktopSidebar: marks the active route with aria-current and has no axe violations", async () => {
  const { container } = render(<DesktopSidebar />);

  const primaryNav = screen.getByRole("navigation", { name: /primary/i });
  const activeLink = within(primaryNav).getByRole("link", { name: /check-in/i });
  expect(activeLink).toHaveAttribute("aria-current", "page");

  const homeLink = within(primaryNav).getByRole("link", { name: /^home$/i });
  expect(homeLink).not.toHaveAttribute("aria-current");

  expect(await axe(container)).toHaveNoViolations();
});

test("DesktopSidebar: every primary and secondary nav item is reachable as a link", () => {
  render(<DesktopSidebar />);
  const expectedHrefs = [
    "/",
    "/checkin",
    "/tiny-action",
    "/community",
    "/journal",
    "/professional-help",
    "/safety",
    "/settings",
  ];
  for (const href of expectedHrefs) {
    const links = screen.getAllByRole("link").filter((el) => el.getAttribute("href") === href);
    expect(links.length).toBeGreaterThanOrEqual(1);
  }
});

test("MobileTabBar: safety disclosure links to the Safety Center", () => {
  render(<MobileTabBar />);
  const disclosure = screen.getByText(/not a therapist/i).closest("a");
  expect(disclosure).toHaveAttribute("href", "/safety");
});

test("MobileTabBar: 'More' opens a dialog exposing secondary nav items, no axe violations", async () => {
  const { container } = render(<MobileTabBar />);

  // Secondary items are not present until "More" is opened.
  expect(screen.queryByRole("dialog")).not.toBeInTheDocument();

  fireEvent.click(screen.getByRole("button", { name: /more/i }));

  const dialog = await screen.findByRole("dialog", { name: /more/i });
  expect(within(dialog).getByRole("link", { name: /professional help/i })).toHaveAttribute(
    "href",
    "/professional-help"
  );
  expect(within(dialog).getByRole("link", { name: /safety center/i })).toHaveAttribute(
    "href",
    "/safety"
  );
  expect(within(dialog).getByRole("link", { name: /settings/i })).toHaveAttribute(
    "href",
    "/settings"
  );

  expect(await axe(container)).toHaveNoViolations();
});

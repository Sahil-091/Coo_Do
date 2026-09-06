import { render, screen } from "@testing-library/react";
import { axe } from "jest-axe";
import { beforeEach, describe, expect, test, vi } from "vitest";

vi.mock("@/lib/auth/dal", () => ({
  requireOnboardedUser: vi.fn(async () => ({
    userId: "user-123",
    email: "student@example.com",
    ageVerified: true,
    pseudonymousDisplayName: "Quiet Fox",
  })),
}));

vi.mock("@/lib/auth/actions", () => ({
  logoutAction: vi.fn(),
  updatePrivacySettingsAction: vi.fn(async () => ({})),
  requestDataAction: vi.fn(async () => ({})),
  submitConsentAction: vi.fn(async () => ({})),
}));

vi.mock("@/lib/core-api-server", () => ({
  internalApiFetch: vi.fn(async (path: string) => {
    if (path.endsWith("/consents")) {
      return [
        { consent_type: "ai_chat", granted: false, updated_at: null },
        { consent_type: "anonymous_community", granted: true, updated_at: "2026-01-01T00:00:00Z" },
        { consent_type: "matching_visibility", granted: false, updated_at: null },
        { consent_type: "institutional_data_sharing", granted: false, updated_at: null },
      ];
    }
    if (path.endsWith("/privacy-settings")) {
      return {
        profile_visible_in_matching: false,
        display_name_visible_in_rooms: false,
        updated_at: "2026-01-01T00:00:00Z",
      };
    }
    if (path.endsWith("/data-requests")) {
      return [];
    }
    throw new Error(`Unexpected path in test mock: ${path}`);
  }),
}));

describe("Settings / Privacy Center page", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  test("renders account info, all 4 consent toggles, and has no axe violations", async () => {
    const { default: SettingsPage } = await import("../src/app/(app)/settings/page");
    const element = await SettingsPage();
    const { container } = render(element);

    expect(screen.getByText("student@example.com")).toBeInTheDocument();
    expect(screen.getByText("Quiet Fox")).toBeInTheDocument();

    // All 4 consent types render as switches, reflecting the mocked state.
    const switches = screen.getAllByRole("switch");
    // 4 consent toggles + 2 privacy-visibility toggles = 6
    expect(switches).toHaveLength(6);

    const anonymousCommunitySwitch = screen.getByRole("switch", {
      name: /anonymous community rooms/i,
    });
    expect(anonymousCommunitySwitch).toHaveAttribute("aria-checked", "true");

    const aiChatSwitch = screen.getByRole("switch", { name: /ai companion chat/i });
    expect(aiChatSwitch).toHaveAttribute("aria-checked", "false");

    expect(await axe(container)).toHaveNoViolations();
  });

  test("renders a logout form pointing at the logout action", async () => {
    const { default: SettingsPage } = await import("../src/app/(app)/settings/page");
    const element = await SettingsPage();
    render(element);
    expect(screen.getByRole("button", { name: /log out/i })).toBeInTheDocument();
  });
});

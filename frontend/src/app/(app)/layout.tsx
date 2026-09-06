import { AppShell } from "@/components/AppShell/AppShell";
import { requireOnboardedUser } from "@/lib/auth/dal";

export default async function AppLayout({ children }: LayoutProps<"/">) {
  // The real gate (R&D doc Section 11/17). proxy.ts's check is
  // optimistic (JWT-only); this one hits core-api fresh, every time,
  // for every (app) route — see lib/auth/dal.ts for why that matters
  // specifically for age_verified.
  await requireOnboardedUser();

  return <AppShell>{children}</AppShell>;
}

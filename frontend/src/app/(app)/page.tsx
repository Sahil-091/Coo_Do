import { BookOpen, Footprints, Sparkles, type LucideIcon } from "lucide-react";
import Link from "next/link";
import { Card, CardDescription, CardHeader, CardTitle } from "@/components/ui/Card";

const shortcuts: { href: string; icon: LucideIcon; title: string; description: string }[] = [
  {
    href: "/checkin",
    icon: Sparkles,
    title: "Check in",
    description: "60 seconds to name how you're feeling and what you need.",
  },
  {
    href: "/tiny-action",
    icon: Footprints,
    title: "Try a tiny action",
    description: "One small, real-world step — not a whole plan.",
  },
  {
    href: "/journal",
    icon: BookOpen,
    title: "Open your journal",
    description: "See what's actually changed over time.",
  },
];

export default function HomePage() {
  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="font-display text-2xl text-ink">Welcome back</h1>
        <p className="mt-1 text-sm text-ink-muted">
          This is your home base — small, real steps, whenever you&rsquo;re ready for one.
        </p>
      </div>

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {shortcuts.map(({ href, icon: Icon, title, description }) => (
          <Link key={href} href={href} className="group block">
            <Card className="h-full transition-colors group-hover:bg-paper">
              <CardHeader>
                <span className="mb-1 flex h-9 w-9 items-center justify-center rounded-full bg-lamp-tint">
                  <Icon className="h-5 w-5 text-lamp" aria-hidden="true" />
                </span>
                <CardTitle as="h2">{title}</CardTitle>
              </CardHeader>
              <CardDescription>{description}</CardDescription>
            </Card>
          </Link>
        ))}
      </div>
    </div>
  );
}

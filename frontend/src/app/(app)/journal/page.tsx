import { requireOnboardedUser } from "@/lib/auth/dal";
import { internalApiFetch } from "@/lib/core-api-server";
import { JournalComposer } from "./JournalComposer";
import { JournalControls } from "./JournalControls";
import { JournalEntryList } from "./JournalEntryList";
import type { JournalExportEntry } from "./actions";

interface Comparison {
  window_days: number;
  narrative: string;
}

interface Indicator {
  key: string;
  sentence: string;
}

interface JournalPageData {
  entries: JournalExportEntry[];
  comparisons: Comparison[];
  indicators: Indicator[];
}

async function getJournalPageData(userId: string): Promise<JournalPageData | null> {
  try {
    const [entries, comparisons, indicators] = await Promise.all([
      internalApiFetch<JournalExportEntry[]>(`/internal/users/${userId}/journal`),
      internalApiFetch<Comparison[]>(`/internal/users/${userId}/journal/comparisons`),
      internalApiFetch<Indicator[]>(`/internal/users/${userId}/real-life-indicators`),
    ]);
    return { entries, comparisons, indicators };
  } catch {
    return null;
  }
}

export default async function JournalPage() {
  const user = await requireOnboardedUser();
  const data = await getJournalPageData(user.userId);

  if (!data) {
    return (
      <div className="mx-auto max-w-3xl space-y-4 pb-8">
        <header>
          <p className="text-sm font-semibold text-lamp">PRIVATE JOURNAL</p>
          <h1 className="mt-1 font-display text-3xl text-ink">What&apos;s changing, in your own words</h1>
        </header>
        <p role="alert" className="rounded-xl border border-clay/20 bg-clay-tint p-4 text-sm text-clay">
          Your private journal is temporarily unavailable. Nothing was saved or deleted. Please try again shortly.
        </p>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-3xl space-y-7 pb-8">
      <header>
        <p className="text-sm font-semibold text-lamp">PRIVATE JOURNAL</p>
        <h1 className="mt-1 font-display text-3xl text-ink">What&apos;s changing, in your own words</h1>
        <p className="mt-2 text-sm leading-6 text-ink-muted">
          Only you can read these reflections. They are encrypted at rest and never turned into a score.
        </p>
      </header>
      <JournalComposer />
      <section>
        <h2 className="font-display text-xl text-ink">Looking back</h2>
        <div className="mt-3 space-y-3">
          {data.comparisons.map((item) => (
            <article key={item.window_days} className="rounded-xl border border-border-subtle bg-paper-raised p-4">
              <h3 className="text-sm font-semibold text-ink">Last {item.window_days} days</h3>
              <p className="mt-1 text-sm leading-6 text-ink-muted">{item.narrative}</p>
            </article>
          ))}
        </div>
      </section>
      <section>
        <h2 className="font-display text-xl text-ink">Real-life indicators</h2>
        <p className="mt-1 text-sm text-ink-muted">Separate actions, never combined into one score.</p>
        <ul className="mt-3 space-y-2">
          {data.indicators.map((item) => (
            <li key={item.key} className="rounded-lg border border-border-subtle bg-white px-4 py-3 text-sm text-ink">
              {item.sentence}
            </li>
          ))}
        </ul>
      </section>
      <section>
        <h2 className="font-display text-xl text-ink">Your reflections</h2>
        <JournalEntryList entries={data.entries} />
      </section>
      <JournalControls hasEntries={data.entries.length > 0} />
    </div>
  );
}

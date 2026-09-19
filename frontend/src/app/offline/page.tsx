export default function OfflinePage() {
  return (
    <main className="flex min-h-full flex-1 flex-col items-center justify-center gap-3 px-6 text-center">
      <h1 className="text-xl font-semibold text-neutral-800">
        You&rsquo;re offline
      </h1>
      <p className="max-w-sm text-sm text-neutral-500">
        This page is served from the app shell cache. Once your connection
        is back, the rest of the app will load normally.
      </p>
    </main>
  );
}

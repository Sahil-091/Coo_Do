export default function OnboardingLayout({ children }: LayoutProps<"/">) {
  return (
    <div className="flex min-h-dvh flex-col items-center bg-paper px-4 py-10">
      <span className="font-display mb-8 text-xl text-ink">Campus Connect</span>
      <div className="w-full max-w-sm">{children}</div>
    </div>
  );
}

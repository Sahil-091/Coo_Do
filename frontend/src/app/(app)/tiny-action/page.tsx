import { getSuggestionAction } from "@/lib/tiny-action/actions";
import { TinyActionFlow } from "./TinyActionFlow";

export default async function TinyActionPage({ searchParams }: PageProps<"/tiny-action">) {
  const params = await searchParams;
  const checkinIdParam = params.checkinId;
  const checkinId = typeof checkinIdParam === "string" ? checkinIdParam : undefined;

  const suggestion = await getSuggestionAction();

  if ("error" in suggestion) {
    return (
      <div className="mx-auto flex max-w-lg flex-col gap-3 py-8">
        <p role="alert" className="text-sm text-clay">
          {suggestion.error}
        </p>
      </div>
    );
  }

  return <TinyActionFlow initialLadder={suggestion.ladder} checkinId={checkinId} />;
}

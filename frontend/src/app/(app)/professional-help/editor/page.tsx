import { notFound } from "next/navigation";
import { requireOnboardedUser } from "@/lib/auth/dal";
import { internalApiFetch } from "@/lib/core-api-server";
import { serverEnv } from "@/lib/env.server";
import { saveProfessionalResourceAction } from "../actions";

interface ResourceForEditor {
  id: string; resource_key: string; region: string; category: string; title: string; summary: string;
  contact_label: string | null; contact_value: string | null; contact_uri: string | null;
  booking_steps: string[]; what_to_expect: string | null; opening_lines: string[]; last_verified_at: string | null; version: number;
}

function canEdit(email: string) {
  return serverEnv.PROFESSIONAL_HELP_EDITOR_EMAILS?.split(",").map((entry) => entry.trim().toLowerCase()).includes(email.toLowerCase()) ?? false;
}

export default async function ProfessionalHelpEditorPage() {
  const user = await requireOnboardedUser();
  if (!canEdit(user.email)) notFound();
  const resources = await internalApiFetch<ResourceForEditor[]>("/internal/professional-resources?region=India");
  return <div className="mx-auto max-w-3xl space-y-6 pb-8"><header><p className="text-sm font-semibold text-lamp">EDITOR</p><h1 className="mt-1 font-display text-3xl text-ink">Professional-help directory</h1><p className="mt-2 text-sm leading-6 text-ink-muted">Publish only human-reviewed information. Saving an existing entry creates a new version; it never silently rewrites what students previously saw.</p></header><ResourceForm /><section className="space-y-4"><h2 className="font-display text-2xl text-ink">Published entries</h2>{resources.map((resource) => <details key={resource.id} className="rounded-xl border border-border-subtle bg-white p-4"><summary className="cursor-pointer font-semibold text-ink">{resource.title} <span className="ml-2 text-xs font-normal text-ink-muted">version {resource.version}</span></summary><div className="mt-4"><ResourceForm resource={resource} /></div></details>)}</section></div>;
}

function ResourceForm({ resource }: { resource?: ResourceForEditor }) {
  return <form action={saveProfessionalResourceAction} className="space-y-4 rounded-xl border border-border-subtle bg-paper-raised p-5"><input type="hidden" name="resourceId" value={resource?.id ?? ""} /><div><h2 className="font-bold text-ink">{resource ? `Replace ${resource.title}` : "Add a directory entry"}</h2><p className="mt-1 text-xs text-ink-muted">One line per booking step or opening line.</p></div><div className="grid gap-4 sm:grid-cols-2"><Field name="resourceKey" label="Stable key" defaultValue={resource?.resource_key} required readOnly={Boolean(resource)} /><Field name="region" label="Region" defaultValue={resource?.region ?? "India"} required readOnly={Boolean(resource)} /><Field name="category" label="Category" defaultValue={resource?.category} required /><Field name="title" label="Title" defaultValue={resource?.title} required /><Field name="contactLabel" label="Contact label" defaultValue={resource?.contact_label ?? undefined} /><Field name="contactValue" label="Contact value" defaultValue={resource?.contact_value ?? undefined} /><Field name="contactUri" label="Contact URI" defaultValue={resource?.contact_uri ?? undefined} placeholder="tel:14416 or https://…" /><Field name="lastVerifiedAt" label="Last reviewed" defaultValue={resource?.last_verified_at ?? undefined} type="date" /></div><TextArea name="summary" label="Summary" defaultValue={resource?.summary} required /><TextArea name="bookingSteps" label="How to start" defaultValue={resource?.booking_steps.join("\n")} /><TextArea name="whatToExpect" label="What to expect" defaultValue={resource?.what_to_expect ?? undefined} /><TextArea name="openingLines" label="Opening lines" defaultValue={resource?.opening_lines.join("\n")} /><button type="submit" className="rounded-lg bg-lamp px-4 py-2.5 text-sm font-semibold text-white hover:bg-lamp/90">{resource ? "Publish replacement version" : "Publish entry"}</button></form>;
}
function Field({ label, name, defaultValue, required, readOnly, type = "text", placeholder }: { label: string; name: string; defaultValue?: string; required?: boolean; readOnly?: boolean; type?: string; placeholder?: string }) { return <label className="flex flex-col gap-1 text-sm font-medium text-ink">{label}<input name={name} type={type} defaultValue={defaultValue} required={required} readOnly={readOnly} placeholder={placeholder} className="rounded-md border border-border-subtle bg-white px-3 py-2 text-sm font-normal text-ink read-only:bg-paper" /></label>; }
function TextArea({ label, name, defaultValue, required }: { label: string; name: string; defaultValue?: string; required?: boolean }) { return <label className="flex flex-col gap-1 text-sm font-medium text-ink">{label}<textarea name={name} defaultValue={defaultValue} required={required} rows={3} className="rounded-md border border-border-subtle bg-white px-3 py-2 text-sm font-normal leading-5 text-ink" /></label>; }

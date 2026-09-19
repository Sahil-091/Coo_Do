"use client";

import { HeartHandshake, Mail, MessageCircle, Plus, Trash2 } from "lucide-react";
import { useState, useTransition } from "react";
import { Button } from "@/components/ui/Button";
import {
  createTrustedContactAction,
  deleteTrustedContactAction,
  prepareTrustedOutreachAction,
  type TrustedContact,
  type TrustedContactChannel,
  type TrustedContactRelationship,
  type TrustedContactScenario,
} from "./actions";

const SCENARIOS: Record<TrustedContactScenario, string> = {
  feeling_overwhelmed: "When I feel overwhelmed",
  need_to_talk: "When I need someone to talk to",
  practical_support: "When I need practical support",
  urgent_but_not_emergency: "When I need support soon",
};

export function TrustedContactsClient({ initialContacts, initialScenario }: { initialContacts: TrustedContact[]; initialScenario?: TrustedContactScenario }) {
  const [contacts, setContacts] = useState(initialContacts);
  const [displayName, setDisplayName] = useState("");
  const [relationship, setRelationship] = useState<TrustedContactRelationship>("friend");
  const [channel, setChannel] = useState<TrustedContactChannel>("sms");
  const [contactValue, setContactValue] = useState("");
  const [scopes, setScopes] = useState<TrustedContactScenario[]>([initialScenario ?? "need_to_talk"]);
  const [error, setError] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();

  function toggleScope(scope: TrustedContactScenario) {
    setScopes((current) => current.includes(scope) ? current.filter((item) => item !== scope) : [...current, scope]);
  }

  function addContact() {
    setError(null);
    startTransition(async () => {
      const result = await createTrustedContactAction({ displayName, relationship, channel, contactValue, allowedScenarios: scopes });
      if ("error" in result) { setError(result.error); return; }
      setContacts((current) => [result, ...current]);
      setDisplayName(""); setContactValue(""); setScopes([initialScenario ?? "need_to_talk"]);
    });
  }

  function removeContact(contactId: string) {
    setError(null);
    startTransition(async () => {
      const result = await deleteTrustedContactAction(contactId);
      if (result.error) { setError(result.error); return; }
      setContacts((current) => current.filter((contact) => contact.id !== contactId));
    });
  }

  function reachOut(contact: TrustedContact, scenario: TrustedContactScenario) {
    setError(null);
    startTransition(async () => {
      const result = await prepareTrustedOutreachAction(contact.id, scenario);
      if ("error" in result) { setError(result.error); return; }
      // This explicit click only opens the student's own mail/SMS composer.
      // The app never sends a message itself; the student retains final control.
      window.location.assign(result.destination);
    });
  }

  return <div className="mx-auto max-w-3xl space-y-8 pb-8"><header><p className="text-sm font-semibold text-lamp">TRUSTED PEOPLE</p><h1 className="mt-1 font-display text-3xl text-ink">Keep your own support circle close</h1><p className="mt-3 max-w-2xl text-sm leading-6 text-ink-muted">Choose anyone who feels safe for you—friend, parent, sibling, teacher, counselor, mentor, or someone else. Coo_Do never contacts them automatically.</p></header>
    <section aria-labelledby="add-contact" className="rounded-xl border border-border-subtle bg-paper-raised p-5"><div className="flex items-start gap-3"><span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-lamp-tint text-lamp"><Plus className="h-5 w-5" aria-hidden="true" /></span><div><h2 id="add-contact" className="font-display text-xl text-ink">Add a trusted person</h2><p className="mt-1 text-sm text-ink-muted">Their name and contact detail are encrypted. Pick only the situations they are okay being contacted about.</p></div></div><div className="mt-5 grid gap-3 sm:grid-cols-2"><label className="text-sm font-medium text-ink">Name<input value={displayName} onChange={(event) => setDisplayName(event.target.value)} maxLength={80} className="mt-1 block w-full rounded-md border border-border bg-white px-3 py-2" /></label><label className="text-sm font-medium text-ink">Relationship<select value={relationship} onChange={(event) => setRelationship(event.target.value as TrustedContactRelationship)} className="mt-1 block w-full rounded-md border border-border bg-white px-3 py-2"><option value="friend">Friend</option><option value="parent">Parent</option><option value="sibling">Sibling</option><option value="teacher">Teacher</option><option value="counselor">Counselor</option><option value="mentor">Mentor</option><option value="other">Someone else</option></select></label><label className="text-sm font-medium text-ink">Contact by<select value={channel} onChange={(event) => setChannel(event.target.value as TrustedContactChannel)} className="mt-1 block w-full rounded-md border border-border bg-white px-3 py-2"><option value="sms">Text message</option><option value="email">Email</option></select></label><label className="text-sm font-medium text-ink">{channel === "sms" ? "Phone number" : "Email address"}<input value={contactValue} onChange={(event) => setContactValue(event.target.value)} inputMode={channel === "sms" ? "tel" : "email"} className="mt-1 block w-full rounded-md border border-border bg-white px-3 py-2" /></label></div><fieldset className="mt-5"><legend className="text-sm font-medium text-ink">They are okay hearing from me…</legend><p className="mt-1 text-xs text-ink-muted">Choose at least one. This is not blanket permission.</p><div className="mt-3 grid gap-2 sm:grid-cols-2">{(Object.keys(SCENARIOS) as TrustedContactScenario[]).map((scope) => <label key={scope} className="flex cursor-pointer items-center gap-2 rounded-lg border border-border-subtle p-3 text-sm text-ink"><input type="checkbox" checked={scopes.includes(scope)} onChange={() => toggleScope(scope)} />{SCENARIOS[scope]}</label>)}</div></fieldset><Button type="button" onClick={addContact} disabled={isPending || !displayName.trim() || !contactValue.trim() || scopes.length === 0} className="mt-5">Save trusted person</Button></section>
    {error && <p role="alert" className="rounded-lg border border-clay/20 bg-clay-tint p-3 text-sm text-clay">{error}</p>}
    <section aria-labelledby="saved-contacts"><h2 id="saved-contacts" className="font-display text-2xl text-ink">Your trusted people</h2><p className="mt-1 text-sm text-ink-muted">You choose every outreach in the moment. Opening a draft does not send it.</p>{contacts.length === 0 ? <div className="mt-3 rounded-xl border border-dashed border-border bg-paper-raised p-6 text-sm text-ink-muted">No one is saved yet. Adding a person is optional, and it does not notify them.</div> : <ul className="mt-3 space-y-3">{contacts.map((contact) => <li key={contact.id} className="rounded-xl border border-border-subtle bg-paper-raised p-5"><div className="flex items-start justify-between gap-4"><div><h3 className="font-semibold text-ink">{contact.displayName}</h3><p className="mt-1 text-sm text-ink-muted">{contact.relationship} · {contact.channel === "sms" ? "Text message" : "Email"}</p></div><Button type="button" variant="quiet-destructive" size="sm" aria-label={`Remove ${contact.displayName}`} onClick={() => removeContact(contact.id)} disabled={isPending}><Trash2 className="h-4 w-4" aria-hidden="true" />Remove</Button></div><div className="mt-4 flex flex-wrap gap-2">{contact.allowedScenarios.map((scenario) => <Button key={scenario} type="button" variant="secondary" size="sm" onClick={() => reachOut(contact, scenario)} disabled={isPending}>{contact.channel === "sms" ? <MessageCircle className="h-4 w-4" aria-hidden="true" /> : <Mail className="h-4 w-4" aria-hidden="true" />} {SCENARIOS[scenario]}</Button>)}</div></li>)}</ul>}</section>
    <aside className="rounded-xl border border-lamp/20 bg-lamp-tint p-4 text-sm leading-6 text-ink"><HeartHandshake className="mb-2 h-5 w-5 text-lamp" aria-hidden="true" />If you&apos;re in immediate danger or might harm yourself, use the Safety Center for urgent resources. Reaching out here is always your choice and never replaces emergency support.</aside></div>;
}

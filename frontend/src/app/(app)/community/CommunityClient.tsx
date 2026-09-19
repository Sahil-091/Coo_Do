"use client";

import { Camera, Headphones, Plus, UsersRound, VideoOff } from "lucide-react";
import { useEffect, useRef, useState, useTransition } from "react";
import { Button } from "@/components/ui/Button";
import { env } from "@/lib/env";
import {
  createActivityAction,
  joinActivityAction,
  savePresenceFeedbackAction,
  type ActivityRoom,
  type ActivityTopic,
} from "./actions";

const TOPICS: Record<ActivityTopic, { label: string; detail: string }> = {
  study: { label: "Study together", detail: "Quiet company for your own study." },
  coding: { label: "Code alongside", detail: "A calm co-working room for coding." },
  reading: { label: "Read alongside", detail: "Bring any book, article, or notes." },
  writing: { label: "Write together", detail: "A little shared momentum for writing." },
  quiet_work: { label: "Quiet work", detail: "For any task that feels easier near others." },
};

function websocketUrl(roomId: string, token: string) {
  const base = env.NEXT_PUBLIC_CORE_API_URL.replace(/^http/, "ws");
  return `${base}/internal/users/presence-rooms/${roomId}/ws?token=${encodeURIComponent(token)}`;
}

function formatStart(value: string | null) {
  if (!value) return "Starting now";
  return new Intl.DateTimeFormat(undefined, { dateStyle: "medium", timeStyle: "short" }).format(new Date(value));
}

export function CommunityClient({ initialActivities }: { initialActivities: ActivityRoom[] }) {
  const [activities, setActivities] = useState(initialActivities);
  const [topic, setTopic] = useState<ActivityTopic>("study");
  const [scheduledFor, setScheduledFor] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [session, setSession] = useState<{ activity: ActivityRoom; roomId: string; token: string; count: number } | null>(null);
  const [isPending, startTransition] = useTransition();

  function createRoom() {
    setError(null);
    startTransition(async () => {
      const result = await createActivityAction(topic, scheduledFor || undefined);
      if ("error" in result) {
        setError(result.error);
        return;
      }
      setActivities((items) => [result, ...items]);
      setScheduledFor("");
    });
  }

  function join(activity: ActivityRoom) {
    setError(null);
    startTransition(async () => {
      const result = await joinActivityAction(activity.id);
      if ("error" in result) {
        setError(result.error);
        return;
      }
      setSession({ activity, roomId: result.roomId, token: result.token, count: result.headcount });
    });
  }

  if (session) {
    return <PresenceSession session={session} onLeave={() => setSession(null)} />;
  }

  return (
    <div className="mx-auto max-w-4xl space-y-8 pb-8">
      <header className="max-w-2xl">
        <p className="text-sm font-semibold text-lamp">SHARED PRESENCE</p>
        <h1 className="mt-1 font-display text-3xl text-ink">Be around people, with no pressure to interact</h1>
        <p className="mt-3 text-sm leading-6 text-ink-muted">
          Many students find quiet company helps them feel less alone while working. There is no chat, no participant list, and no location sharing here.
        </p>
      </header>

      <section aria-labelledby="create-room" className="rounded-xl border border-border-subtle bg-paper-raised p-5">
        <div className="flex items-start gap-3"><span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-lamp-tint text-lamp"><Plus className="h-5 w-5" aria-hidden="true" /></span><div><h2 id="create-room" className="font-display text-xl text-ink">Start a virtual room</h2><p className="mt-1 text-sm text-ink-muted">Pick a topic. Rooms are virtual only—never tied to a campus location.</p></div></div>
        <div className="mt-4 grid gap-3 sm:grid-cols-[1fr_auto_auto]">
          <label className="text-sm font-medium text-ink">Activity<select value={topic} onChange={(event) => setTopic(event.target.value as ActivityTopic)} className="mt-1 block w-full rounded-md border border-border bg-white px-3 py-2 text-sm"><option value="study">Study together</option><option value="coding">Code alongside</option><option value="reading">Read alongside</option><option value="writing">Write together</option><option value="quiet_work">Quiet work</option></select></label>
          <label className="text-sm font-medium text-ink">Schedule (optional)<input type="datetime-local" value={scheduledFor} min={new Date().toISOString().slice(0, 16)} onChange={(event) => setScheduledFor(event.target.value)} className="mt-1 block rounded-md border border-border bg-white px-3 py-2 text-sm" /></label>
          <Button type="button" onClick={createRoom} disabled={isPending} className="self-end">Create room</Button>
        </div>
      </section>

      {error && <p role="alert" className="rounded-lg border border-clay/20 bg-clay-tint p-3 text-sm text-clay">{error}</p>}

      <section aria-labelledby="rooms-heading"><div className="flex items-center justify-between"><h2 id="rooms-heading" className="font-display text-2xl text-ink">Open rooms</h2><span className="text-sm text-ink-muted">Anonymous headcounts only</span></div>
        {activities.length === 0 ? <div className="mt-3 rounded-xl border border-dashed border-border bg-paper-raised p-6 text-sm text-ink-muted">No rooms are open yet. You can start a quiet one whenever you like.</div> : <ul className="mt-3 grid gap-3 sm:grid-cols-2">{activities.map((activity) => <li key={activity.id} className="rounded-xl border border-border-subtle bg-paper-raised p-5"><div className="flex items-start justify-between gap-4"><div><h3 className="font-semibold text-ink">{TOPICS[activity.topic].label}</h3><p className="mt-1 text-sm leading-5 text-ink-muted">{TOPICS[activity.topic].detail}</p></div><span className="inline-flex shrink-0 items-center gap-1 rounded-full bg-lamp-tint px-2.5 py-1 text-xs font-semibold text-lamp"><UsersRound className="h-3.5 w-3.5" aria-hidden="true" />{activity.headcount}</span></div><p className="mt-4 text-xs text-ink-muted">{activity.status === "scheduled" ? `Scheduled for ${formatStart(activity.startsAt)}` : "Open now"}</p><Button type="button" variant="secondary" className="mt-3 w-full" onClick={() => join(activity)} disabled={isPending || activity.status !== "live"}>{activity.status === "live" ? "Join quietly" : "Starts soon"}</Button></li>)}</ul>}
      </section>
    </div>
  );
}

function PresenceSession({ session, onLeave }: { session: { activity: ActivityRoom; roomId: string; token: string; count: number }; onLeave: () => void }) {
  const [headcount, setHeadcount] = useState(session.count);
  const [cameraOn, setCameraOn] = useState(false);
  const [audioOn, setAudioOn] = useState(false);
  const [mediaError, setMediaError] = useState<string | null>(null);
  const [showFeedback, setShowFeedback] = useState(false);
  const [sessionActive, setSessionActive] = useState(true);
  const videoRef = useRef<HTMLVideoElement>(null);
  const socketRef = useRef<WebSocket | null>(null);
  const streamRef = useRef<MediaStream | null>(null);

  useEffect(() => {
    if (!sessionActive) return;
    const socket = new WebSocket(websocketUrl(session.roomId, session.token));
    socketRef.current = socket;
    socket.onmessage = (event) => { try { const update = JSON.parse(event.data); if (update.type === "headcount") setHeadcount(update.count); } catch { /* Ignore malformed count updates. */ } };
    const heartbeat = window.setInterval(() => { if (socket.readyState === WebSocket.OPEN) socket.send("ping"); }, 20000);
    return () => { window.clearInterval(heartbeat); socket.close(); socketRef.current = null; };
  }, [session.roomId, session.token, sessionActive]);

  useEffect(() => {
    async function updatePreview() {
      streamRef.current?.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
      if (!cameraOn && !audioOn) { if (videoRef.current) videoRef.current.srcObject = null; return; }
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ video: cameraOn, audio: audioOn });
        streamRef.current = stream;
        if (videoRef.current) videoRef.current.srcObject = stream;
        setMediaError(null);
      } catch { setMediaError("Your device permission wasn’t available. You can still stay in the room without it."); }
    }
    void updatePreview();
    return () => { streamRef.current?.getTracks().forEach((track) => track.stop()); streamRef.current = null; };
  }, [cameraOn, audioOn]);

  function leave() {
    streamRef.current?.getTracks().forEach((track) => track.stop());
    // Leaving is immediate; the optional reflection happens after the room
    // connection is already closed, never as a barrier to leaving.
    setSessionActive(false);
    setShowFeedback(true);
  }

  async function feedback(value: "less_alone" | "neutral" | "not_for_me" | null) {
    await savePresenceFeedbackAction(session.activity.id, value);
    onLeave();
  }

  if (showFeedback) return <div className="mx-auto max-w-lg space-y-5 py-8"><h1 className="font-display text-3xl text-ink">How did that feel?</h1><p className="text-sm leading-6 text-ink-muted">Optional, private feedback helps us understand the room experience. It is never shown to anyone in the room.</p><div className="grid gap-2"><Button type="button" variant="secondary" onClick={() => feedback("less_alone")}>A little less alone</Button><Button type="button" variant="secondary" onClick={() => feedback("neutral")}>About the same</Button><Button type="button" variant="secondary" onClick={() => feedback("not_for_me")}>Not for me today</Button><Button type="button" variant="ghost" onClick={() => feedback(null)}>Skip</Button></div></div>;

  return <div className="mx-auto max-w-2xl space-y-7 pb-8"><header><p className="text-sm font-semibold text-lamp">PRESENCE MODE</p><h1 className="mt-1 font-display text-3xl text-ink">{TOPICS[session.activity.topic].label}</h1><p className="mt-2 text-sm text-ink-muted">{headcount} {headcount === 1 ? "person is" : "people are"} here quietly. No names or participant list are shared.</p></header><section className="rounded-xl border border-border-subtle bg-paper-raised p-6"><div className="flex min-h-48 items-center justify-center rounded-lg bg-lamp-tint"><div className="text-center text-sm text-ink-muted"><VideoOff className="mx-auto mb-2 h-7 w-7 text-lamp" aria-hidden="true" />Your presence is enough. There is nothing to say or do.</div></div><div className="mt-4 flex flex-wrap gap-2"><Button type="button" variant="secondary" onClick={() => setCameraOn((on) => !on)}><Camera className="mr-2 h-4 w-4" aria-hidden="true" />{cameraOn ? "Turn camera off" : "Camera optional"}</Button><Button type="button" variant="secondary" onClick={() => setAudioOn((on) => !on)}><Headphones className="mr-2 h-4 w-4" aria-hidden="true" />{audioOn ? "Turn audio off" : "Audio optional"}</Button></div><p className="mt-3 text-xs leading-5 text-ink-muted">Camera and audio are off by default. If you turn either on, it stays as a preview on your device—Presence Mode does not transmit audio or video.</p>{mediaError && <p role="alert" className="mt-2 text-sm text-clay">{mediaError}</p>}<video ref={videoRef} muted autoPlay playsInline className={cameraOn ? "mt-4 aspect-video w-full rounded-lg bg-ink object-cover" : "hidden"} /></section><Button type="button" onClick={leave}>Leave room</Button></div>;
}

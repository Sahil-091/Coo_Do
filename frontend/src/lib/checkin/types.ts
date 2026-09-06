export const FEELINGS = [
  "lonely",
  "sad",
  "anxious",
  "overwhelmed",
  "angry",
  "empty",
  "exhausted",
  "unmotivated",
  "confused",
  "dont_know",
] as const;
export type Feeling = (typeof FEELINGS)[number];

export const FEELING_LABELS: Record<Feeling, string> = {
  lonely: "Lonely",
  sad: "Sad",
  anxious: "Anxious",
  overwhelmed: "Overwhelmed",
  angry: "Angry",
  empty: "Empty",
  exhausted: "Exhausted",
  unmotivated: "Unmotivated",
  confused: "Confused",
  dont_know: "Don't know",
};

export const NEEDS = [
  "talk",
  "distraction",
  "understand_feeling",
  "get_motivated",
  "be_around_people",
  "study",
  "relax",
  "ask_for_help",
] as const;
export type Need = (typeof NEEDS)[number];

export const NEED_LABELS: Record<Need, string> = {
  talk: "Someone to talk to",
  distraction: "Get my mind off things",
  understand_feeling: "Understand what I'm feeling",
  get_motivated: "Get motivated",
  be_around_people: "Be around people",
  study: "Study",
  relax: "Relax",
  ask_for_help: "Ask for help",
};

export type TimeOfDay = "morning" | "afternoon" | "evening" | "night";

export type SuggestedPath = "tiny_action" | "presence_mode" | "professional_help";

export const PATH_DESTINATIONS: Record<SuggestedPath, { href: string; cta: string }> = {
  tiny_action: { href: "/tiny-action", cta: "See your tiny action" },
  presence_mode: { href: "/community", cta: "Find people nearby" },
  professional_help: { href: "/professional-help", cta: "See how to get help" },
};

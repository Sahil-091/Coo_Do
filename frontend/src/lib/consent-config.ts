import type { ConsentType } from "./auth/validation";

export const CONSENT_ITEMS: { type: ConsentType; title: string; description: string }[] = [
  {
    type: "ai_chat",
    title: "AI companion chat",
    description:
      "Lets you talk with the AI navigator once it's available. Never required to use the rest of the app.",
  },
  {
    type: "anonymous_community",
    title: "Anonymous community rooms",
    description:
      "Lets you post and read in situation-based rooms once they're live, without revealing your identity.",
  },
  {
    type: "matching_visibility",
    title: "Matching visibility",
    description:
      "Lets other students' searches find you, once Find Someone Like Me is available. Never used for dating.",
  },
  {
    type: "institutional_data_sharing",
    title: "Institutional data sharing",
    description:
      "Only ever de-identified, aggregate data — and only if your campus becomes a partner. Never your individual check-ins, journal, or chats.",
  },
];

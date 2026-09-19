export interface TinyActionRung {
  id: string;
  difficultyLevel: number;
  title: string;
  description: string;
  voiceMessage: string;
}

export type AttemptStatus = "completed" | "skipped" | "reduced";

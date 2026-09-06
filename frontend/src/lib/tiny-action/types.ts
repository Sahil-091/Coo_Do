export interface TinyActionRung {
  id: string;
  difficultyLevel: number;
  title: string;
  description: string;
}

export type AttemptStatus = "completed" | "skipped" | "reduced";

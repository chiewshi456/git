export type SafetyCategory =
  | "sexual"
  | "hate"
  | "violence"
  | "illegal"
  | "privacy"
  | "prompt_injection"
  | "self_harm"
  | "political_sensitive"
  | "spam";

export interface SafetyResult {
  safe: boolean;
  category?: SafetyCategory;
  reason?: string;
  replacement?: string;
}

export interface SafetyLog {
  id: string;
  timestamp: number;
  direction: "input" | "output";
  text: string;
  result: SafetyResult;
}

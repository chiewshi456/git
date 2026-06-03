import type { ChatMessage } from "../chat/types.js";
import type { StreamState } from "../controller/StreamState.js";
import type { MemoryWrite, UserMemory } from "../memory/memoryTypes.js";

export type Emotion =
  | "neutral"
  | "happy"
  | "teasing"
  | "confused"
  | "awkward"
  | "serious"
  | "sleepy";

export type Gesture =
  | "none"
  | "tilt_head"
  | "wave"
  | "shake_head"
  | "nod"
  | "panic";

export type ObsAction =
  | "none"
  | "highlight_chat"
  | "show_safe_skip"
  | "show_thinking"
  | "switch_idle"
  | "play_sfx";

export interface Persona {
  name: string;
  identity: string;
  selfAwareness: string;
  personality: string[];
  catchphrases: string[];
  streamStyle: string[];
  forbiddenTopics: string[];
}

export interface StreamMemorySummary {
  userCount: number;
  recentEvents: string[];
  recentReplies: string[];
}

export interface BrainInput {
  persona: Persona;
  selectedMessage: ChatMessage;
  recentMessages: ChatMessage[];
  userMemory: UserMemory | null;
  streamMemory: StreamMemorySummary;
  streamState: StreamState;
}

export interface BrainOutput {
  replyTo: string | null;
  speak: string;
  emotion: Emotion;
  gesture: Gesture;
  obsAction: ObsAction;
  memoryWrite?: MemoryWrite;
  safety: "safe" | "needs_review" | "blocked";
  decisionReason: string;
}

export interface BrainProviderInfo {
  provider: "mock" | "ollama" | "mika_brain_v3";
  mode: "mock" | "local_llm" | "local_brain";
  model: string;
  baseUrl?: string;
  temperature?: number;
  numCtx?: number;
  timeoutMs?: number;
  pythonCommand?: string;
  llm?: "ollama" | "off";
}

export interface BrainProvider {
  generate(input: BrainInput): BrainOutput;
  generateAsync?(input: BrainInput): Promise<BrainOutput>;
  getInfo?(): BrainProviderInfo;
}

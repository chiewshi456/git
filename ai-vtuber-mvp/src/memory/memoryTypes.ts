export interface UserMemory {
  userId: string;
  username: string;
  seenCount: number;
  lastSeen: number;
  jokes: string[];
  preferences: string[];
  riskNotes: string[];
}

export interface StreamEvent {
  id: string;
  timestamp: number;
  content: string;
}

export interface RecentReply {
  id: string;
  timestamp: number;
  speak: string;
  replyTo: string | null;
}

export interface MemoryStore {
  users: Record<string, UserMemory>;
  streamEvents: StreamEvent[];
  recentReplies: RecentReply[];
}

export interface MemoryWrite {
  type: "user_preference" | "user_joke" | "stream_event" | "risk_note";
  userId?: string;
  content: string;
}

export interface MemoryLog {
  id: string;
  timestamp: number;
  action: string;
  content: string;
}

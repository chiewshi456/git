export type ChatMessageType = "chat" | "gift" | "superchat";

export interface ChatMessage {
  id: string;
  userId: string;
  username: string;
  text: string;
  type: ChatMessageType;
  amount?: number;
  timestamp: number;
}

export interface MessageSelection {
  selectedMessage: ChatMessage | null;
  score: number;
  reasons: string[];
}

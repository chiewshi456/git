import { existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import type { MemoryLog, MemoryStore, MemoryWrite, RecentReply, UserMemory } from "./memoryTypes.js";
import type { BrainOutput, StreamMemorySummary } from "../brain/types.js";
import { createId } from "../utils/ids.js";

const __dirname = dirname(fileURLToPath(import.meta.url));
const defaultMemoryPath = resolve(__dirname, "..", "..", "data", "memory.json");

const emptyStore: MemoryStore = {
  users: {},
  streamEvents: [],
  recentReplies: []
};

export class MemoryModule {
  private store: MemoryStore = structuredClone(emptyStore);
  private logs: MemoryLog[] = [];

  constructor(private readonly memoryPath = defaultMemoryPath) {}

  loadMemory(): MemoryStore {
    if (!existsSync(this.memoryPath)) {
      this.store = structuredClone(emptyStore);
      this.saveMemory();
      return this.store;
    }

    this.store = {
      ...structuredClone(emptyStore),
      ...(JSON.parse(readFileSync(this.memoryPath, "utf-8")) as MemoryStore)
    };
    return this.store;
  }

  saveMemory(): void {
    mkdirSync(dirname(this.memoryPath), { recursive: true });
    writeFileSync(this.memoryPath, `${JSON.stringify(this.store, null, 2)}\n`, "utf-8");
  }

  getUserMemory(userId: string): UserMemory | null {
    return this.store.users[userId] ?? null;
  }

  writeMemory(memoryWrite: MemoryWrite): void {
    if (memoryWrite.type === "stream_event") {
      this.store.streamEvents.unshift({
        id: createId("event"),
        timestamp: Date.now(),
        content: memoryWrite.content
      });
      this.store.streamEvents = this.store.streamEvents.slice(0, 50);
      this.log("stream_event", memoryWrite.content);
      this.saveMemory();
      return;
    }

    if (!memoryWrite.userId) {
      return;
    }

    const user = this.ensureUser(memoryWrite.userId, memoryWrite.userId);
    if (memoryWrite.type === "user_joke" && !user.jokes.includes(memoryWrite.content)) {
      user.jokes.unshift(memoryWrite.content);
      user.jokes = user.jokes.slice(0, 10);
    }

    if (memoryWrite.type === "user_preference" && !user.preferences.includes(memoryWrite.content)) {
      user.preferences.unshift(memoryWrite.content);
      user.preferences = user.preferences.slice(0, 10);
    }

    if (memoryWrite.type === "risk_note") {
      user.riskNotes.unshift(memoryWrite.content);
      user.riskNotes = user.riskNotes.slice(0, 10);
    }

    this.log(memoryWrite.type, memoryWrite.content);
    this.saveMemory();
  }

  recordUserSeen(userId: string, username: string): UserMemory {
    const user = this.ensureUser(userId, username);
    user.username = username;
    user.seenCount += 1;
    user.lastSeen = Date.now();
    this.log("user_seen", `${username} 出现次数：${user.seenCount}`);
    this.saveMemory();
    return user;
  }

  recordReply(output: BrainOutput): void {
    const reply: RecentReply = {
      id: createId("reply"),
      timestamp: Date.now(),
      speak: output.speak,
      replyTo: output.replyTo
    };
    this.store.recentReplies.unshift(reply);
    this.store.recentReplies = this.store.recentReplies.slice(0, 20);
    this.log("reply", output.speak);
    this.saveMemory();
  }

  summarizeRecentMemory(): StreamMemorySummary {
    return {
      userCount: Object.keys(this.store.users).length,
      recentEvents: this.store.streamEvents.slice(0, 5).map((event) => event.content),
      recentReplies: this.store.recentReplies.slice(0, 5).map((reply) => reply.speak)
    };
  }

  getLogs(): MemoryLog[] {
    return this.logs.slice(0, 30);
  }

  clearContext(): void {
    this.store.streamEvents = [];
    this.store.recentReplies = [];
    this.logs = [];
    this.log("clear_context", "已清空本场上下文，保留用户出现次数和长期记忆");
    this.saveMemory();
  }

  private ensureUser(userId: string, username: string): UserMemory {
    if (!this.store.users[userId]) {
      this.store.users[userId] = {
        userId,
        username,
        seenCount: 0,
        lastSeen: Date.now(),
        jokes: [],
        preferences: [],
        riskNotes: []
      };
    }
    return this.store.users[userId];
  }

  private log(action: string, content: string): void {
    this.logs.unshift({
      id: createId("memlog"),
      timestamp: Date.now(),
      action,
      content
    });
    this.logs = this.logs.slice(0, 40);
  }
}

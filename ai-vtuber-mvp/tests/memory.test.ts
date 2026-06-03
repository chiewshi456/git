import assert from "node:assert/strict";
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { resolve } from "node:path";
import test from "node:test";
import { MemoryModule } from "../src/memory/MemoryModule.js";
import type { BrainOutput } from "../src/brain/types.js";
import type { MemoryStore } from "../src/memory/memoryTypes.js";

const tmpDir = resolve(process.cwd(), "tests", ".tmp");
const memoryPath = resolve(tmpDir, "memory.test.json");

function resetTestMemory(): MemoryModule {
  mkdirSync(tmpDir, { recursive: true });
  writeFileSync(memoryPath, JSON.stringify({ users: {}, streamEvents: [], recentReplies: [] }, null, 2), "utf-8");
  const memory = new MemoryModule(memoryPath);
  memory.loadMemory();
  return memory;
}

function store(): MemoryStore {
  return JSON.parse(readFileSync(memoryPath, "utf-8")) as MemoryStore;
}

function output(index: number): BrainOutput {
  return {
    replyTo: `msg-${index}`,
    speak: `reply ${index}`,
    emotion: "neutral",
    gesture: "none",
    obsAction: "none",
    safety: "safe",
    decisionReason: "test output"
  };
}

test("recordUserSeen updates user count and last seen", () => {
  const memory = resetTestMemory();

  memory.recordUserSeen("u1", "KokoFan");
  memory.recordUserSeen("u1", "KokoFan");

  const user = memory.getUserMemory("u1");
  assert.equal(user?.seenCount, 2);
  assert.equal(user?.username, "KokoFan");
  assert.equal(typeof user?.lastSeen, "number");
});

test("writeMemory records user jokes, preferences, risk notes, and stream events", () => {
  const memory = resetTestMemory();

  memory.recordUserSeen("u1", "KokoFan");
  memory.writeMemory({ type: "user_joke", userId: "u1", content: "cached joke" });
  memory.writeMemory({ type: "user_preference", userId: "u1", content: "likes teasing" });
  memory.writeMemory({ type: "risk_note", userId: "u1", content: "unsafe request" });
  memory.writeMemory({ type: "stream_event", content: "stream started" });

  const user = memory.getUserMemory("u1");
  assert.deepEqual(user?.jokes, ["cached joke"]);
  assert.deepEqual(user?.preferences, ["likes teasing"]);
  assert.deepEqual(user?.riskNotes, ["unsafe request"]);
  assert.equal(store().streamEvents[0].content, "stream started");
});

test("recordReply keeps only the latest 20 replies", () => {
  const memory = resetTestMemory();

  for (let index = 0; index < 25; index += 1) {
    memory.recordReply(output(index));
  }

  const replies = store().recentReplies;
  assert.equal(replies.length, 20);
  assert.equal(replies[0].speak, "reply 24");
  assert.equal(replies.at(-1)?.speak, "reply 5");
});

test("summarizeRecentMemory returns compact dashboard-friendly summary", () => {
  const memory = resetTestMemory();

  memory.recordUserSeen("u1", "KokoFan");
  memory.writeMemory({ type: "stream_event", content: "event one" });
  memory.recordReply(output(1));

  const summary = memory.summarizeRecentMemory();
  assert.equal(summary.userCount, 1);
  assert.deepEqual(summary.recentEvents, ["event one"]);
  assert.deepEqual(summary.recentReplies, ["reply 1"]);
});

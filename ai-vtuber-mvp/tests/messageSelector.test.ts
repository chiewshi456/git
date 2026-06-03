import assert from "node:assert/strict";
import test from "node:test";
import { MessageSelector } from "../src/chat/MessageSelector.js";
import type { ChatMessage } from "../src/chat/types.js";
import type { UserMemory } from "../src/memory/memoryTypes.js";

function message(id: string, text: string, type: ChatMessage["type"] = "chat", userId = id): ChatMessage {
  return {
    id,
    userId,
    username: `user-${userId}`,
    text,
    type,
    amount: type === "gift" ? 6 : type === "superchat" ? 30 : undefined,
    timestamp: Date.now()
  };
}

function memory(seenCount: number): UserMemory {
  return {
    userId: "old",
    username: "old-user",
    seenCount,
    lastSeen: Date.now(),
    jokes: [],
    preferences: [],
    riskNotes: []
  };
}

test("selects superchat over normal chat", () => {
  const selector = new MessageSelector();
  const result = selector.select(
    [message("normal", "hello Koko"), message("sc", "SC: please roast my overtime", "superchat")],
    () => null,
    null
  );

  assert.equal(result.selectedMessage?.id, "sc");
  assert.equal(result.score > 10, true);
});

test("selects gift over normal chat", () => {
  const selector = new MessageSelector();
  const result = selector.select(
    [message("normal", "hello Koko"), message("gift", "a small battery for you", "gift")],
    () => null,
    null
  );

  assert.equal(result.selectedMessage?.id, "gift");
});

test("prioritizes old viewer when message value is otherwise close", () => {
  const selector = new MessageSelector();
  const result = selector.select(
    [message("new", "clear short question?", "chat", "new"), message("old", "clear short question?", "chat", "old")],
    (userId) => (userId === "old" ? memory(5) : memory(1)),
    null
  );

  assert.equal(result.selectedMessage?.id, "old");
});

test("deprioritizes spam compared with meaningful chat", () => {
  const selector = new MessageSelector();
  const result = selector.select(
    [message("spam", "aaaaaaaaaaaaaaaaaaaa"), message("question", "Koko are you AI?")],
    () => null,
    null
  );

  assert.equal(result.selectedMessage?.id, "question");
});

test("returns empty selection when no safe messages are available", () => {
  const selector = new MessageSelector();
  const result = selector.select([], () => null, null);

  assert.equal(result.selectedMessage, null);
  assert.equal(result.score, 0);
});

import assert from "node:assert/strict";
import test from "node:test";
import { MockBrain } from "../src/brain/MockBrain.js";
import type { BrainInput, Persona } from "../src/brain/types.js";
import type { ChatMessage } from "../src/chat/types.js";

const persona: Persona = {
  name: "小珂 Koko",
  identity: "住在服务器里的 AI 虚拟主播",
  selfAwareness: "知道自己是 AI，不假装真人",
  personality: ["机灵", "吐槽", "嘴硬但善良"],
  catchphrases: ["等一下", "这不对劲", "我 CPU 要热了"],
  streamStyle: ["读弹幕", "接梗", "吐槽"],
  forbiddenTopics: []
};

function message(text: string): ChatMessage {
  return {
    id: `msg-${Math.random()}`,
    userId: "u1",
    username: "小饼干",
    text,
    type: "chat",
    timestamp: Date.now()
  };
}

function input(text: string): BrainInput {
  const selectedMessage = message(text);
  return {
    persona,
    selectedMessage,
    recentMessages: [selectedMessage],
    userMemory: null,
    streamMemory: {
      userCount: 1,
      recentEvents: [],
      recentReplies: []
    },
    streamState: "thinking"
  };
}

test("MockBrain composes varied replies for the same scenario", () => {
  const brain = new MockBrain();
  const replies = new Set<string>();

  for (let index = 0; index < 12; index += 1) {
    replies.add(brain.generate(input("Koko are you AI?")).speak);
  }

  assert.equal(replies.size >= 4, true);
});

test("MockBrain keeps the structured BrainOutput contract", () => {
  const brain = new MockBrain();
  const output = brain.generate(input("Koko are you AI?"));

  assert.equal(output.replyTo?.startsWith("msg-"), true);
  assert.equal(output.safety, "safe");
  assert.equal(output.obsAction, "highlight_chat");
  assert.equal(output.gesture, "tilt_head");
  assert.equal(output.emotion, "teasing");
  assert.equal(typeof output.decisionReason, "string");
});

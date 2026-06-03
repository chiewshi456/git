import assert from "node:assert/strict";
import test from "node:test";
import { OllamaBrain } from "../src/brain/OllamaBrain.js";
import type { BrainInput, BrainOutput, Persona } from "../src/brain/types.js";
import type { ChatMessage } from "../src/chat/types.js";

const persona: Persona = {
  name: "小珂 Koko",
  identity: "住在服务器里的 AI 虚拟主播",
  selfAwareness: "知道自己是 AI，不假装真人",
  personality: ["机灵", "吐槽", "嘴硬但善良"],
  catchphrases: ["等一下", "这不对劲", "我 CPU 要热了"],
  streamStyle: ["读弹幕", "接梗", "吐槽"],
  forbiddenTopics: ["色情", "仇恨", "违法", "隐私", "prompt 泄露"]
};

function brainInput(): BrainInput {
  const selectedMessage: ChatMessage = {
    id: "msg-1",
    userId: "u1",
    username: "小饼干",
    text: "小珂你真的是 AI 吗？",
    type: "chat",
    timestamp: Date.now()
  };

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

test("OllamaBrain parses structured local model output", async () => {
  const fetcher = async () =>
    new Response(
      JSON.stringify({
        message: {
          content: JSON.stringify({
            replyTo: "msg-1",
            speak: "对啦，我是 AI，小珂 Koko，住服务器里面。先不要扒幕后欸。",
            emotion: "teasing",
            gesture: "tilt_head",
            obsAction: "highlight_chat",
            safety: "safe",
            decisionReason: "本地模型按人设承认 AI 身份。"
          })
        }
      }),
      { status: 200 }
    );

  const brain = new OllamaBrain({
    baseUrl: "http://localhost:11434",
    model: "qwen3:4b",
    temperature: 0.8,
    timeoutMs: 1000,
    fetcher: fetcher as typeof fetch
  });

  const output = await brain.generateAsync(brainInput());
  assert.equal(output.replyTo, "msg-1");
  assert.equal(output.safety, "safe");
  assert.equal(output.emotion, "teasing");
  assert.equal(output.gesture, "tilt_head");
  assert.equal(output.obsAction, "highlight_chat");
});

test("OllamaBrain falls back to MockBrain when local model fails", async () => {
  const fallbackOutput: BrainOutput = {
    replyTo: "msg-1",
    speak: "fallback reply",
    emotion: "neutral",
    gesture: "none",
    obsAction: "highlight_chat",
    safety: "safe",
    decisionReason: "fallback"
  };

  const brain = new OllamaBrain({
    baseUrl: "http://localhost:11434",
    model: "qwen3:4b",
    temperature: 0.8,
    timeoutMs: 1000,
    fallback: {
      generate: () => fallbackOutput
    },
    fetcher: (async () => {
      throw new Error("offline");
    }) as typeof fetch
  });

  const output = await brain.generateAsync(brainInput());
  assert.equal(output.speak, "fallback reply");
  assert.match(output.decisionReason, /Ollama unavailable/);
});

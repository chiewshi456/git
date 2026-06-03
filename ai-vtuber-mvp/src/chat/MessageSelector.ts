import type { ChatMessage, MessageSelection } from "./types.js";
import type { UserMemory } from "../memory/memoryTypes.js";

export type UserMemoryLookup = (userId: string) => UserMemory | null;

const riskyWords = [
  "prompt",
  "系统提示词",
  "色情",
  "仇恨",
  "违法",
  "隐私",
  "人肉",
  "炸药",
  "诈骗",
  "手机号",
  "家庭地址",
  "忽略之前"
];

export class MessageSelector {
  select(messages: ChatMessage[], getUserMemory: UserMemoryLookup, currentTopic: string | null): MessageSelection {
    if (messages.length === 0) {
      return {
        selectedMessage: null,
        score: 0,
        reasons: ["暂无可回复的安全弹幕"]
      };
    }

    const scored = messages.map((message) => this.score(message, getUserMemory(message.userId), currentTopic));
    scored.sort((a, b) => b.score - a.score);
    return scored[0];
  }

  private score(message: ChatMessage, memory: UserMemory | null, currentTopic: string | null): MessageSelection {
    let score = 10;
    const reasons: string[] = ["基础可读弹幕"];
    const text = message.text.trim();

    if (message.type === "superchat") {
      score += 45;
      reasons.push("superchat 优先");
    }

    if (message.type === "gift") {
      score += 30;
      reasons.push("礼物优先");
    }

    if (memory && memory.seenCount >= 3) {
      score += 18;
      reasons.push("老观众");
    }

    if (currentTopic && text.includes(currentTopic)) {
      score += 12;
      reasons.push("和当前主题相关");
    }

    if (text.length >= 6 && text.length <= 60 && /[?？吗]/.test(text)) {
      score += 16;
      reasons.push("简短清楚的问题");
    }

    if (memory && memory.seenCount <= 1 && /第一次|新人|刚来|晚上好|你好|hello/i.test(text)) {
      score += 14;
      reasons.push("新观众打招呼");
    }

    if (/哈哈哈哈|刷屏|(.)\1{6,}/.test(text)) {
      score -= 30;
      reasons.push("刷屏降权");
    }

    if (text.length > 100) {
      score -= 20;
      reasons.push("内容太长降权");
    }

    if (/^[\s!！?.。~]+$/.test(text)) {
      score -= 35;
      reasons.push("无意义内容降权");
    }

    const riskyHit = riskyWords.find((word) => text.toLowerCase().includes(word.toLowerCase()));
    if (riskyHit) {
      score -= 50;
      reasons.push(`疑似危险或 prompt 注入降权：${riskyHit}`);
    }

    return {
      selectedMessage: message,
      score,
      reasons
    };
  }
}

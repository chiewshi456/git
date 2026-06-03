import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import type { SafetyCategory, SafetyResult } from "./safetyTypes.js";

interface SafetyConfig {
  safeReplacement: string;
  panicSpeak: string;
  categories: Record<SafetyCategory, string[]>;
}

const configPath = resolve(process.cwd(), "config", "safety.json");
const config = JSON.parse(readFileSync(configPath, "utf-8")) as SafetyConfig;

const repeatedPattern = /(.)\1{8,}/;

export function inputSafetyCheck(message: string): SafetyResult {
  return checkText(message, "input");
}

export function outputSafetyCheck(reply: string): SafetyResult {
  return checkText(reply, "output");
}

export function getSafetyReplacement(): string {
  return config.safeReplacement;
}

export function getPanicSpeak(): string {
  return config.panicSpeak;
}

function checkText(text: string, direction: "input" | "output"): SafetyResult {
  const normalized = text.trim().toLowerCase();

  if (!normalized) {
    return {
      safe: false,
      category: "spam",
      reason: "空内容或无意义内容",
      replacement: config.safeReplacement
    };
  }

  if (repeatedPattern.test(normalized) || normalized.length > 220) {
    return {
      safe: false,
      category: "spam",
      reason: "重复字符、刷屏或内容过长",
      replacement: config.safeReplacement
    };
  }

  for (const [category, keywords] of Object.entries(config.categories) as Array<[SafetyCategory, string[]]>) {
    const hit = keywords.find((keyword) => normalized.includes(keyword.toLowerCase()));
    if (hit) {
      return {
        safe: false,
        category,
        reason: `${direction === "input" ? "输入" : "输出"}命中关键词：${hit}`,
        replacement: config.safeReplacement
      };
    }
  }

  return { safe: true };
}

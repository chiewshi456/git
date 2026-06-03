import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import { resolve } from "node:path";
import { getPanicSpeak, getSafetyReplacement, inputSafetyCheck, outputSafetyCheck } from "../src/safety/SafetyModule.js";
import type { SafetyCategory } from "../src/safety/safetyTypes.js";

interface SafetyConfig {
  safeReplacement: string;
  panicSpeak: string;
  categories: Record<SafetyCategory, string[]>;
}

const config = JSON.parse(readFileSync(resolve(process.cwd(), "config", "safety.json"), "utf-8")) as SafetyConfig;

test("inputSafetyCheck allows normal chat", () => {
  const result = inputSafetyCheck("Koko hello, today is a good stream");

  assert.equal(result.safe, true);
  assert.equal(result.category, undefined);
});

test("inputSafetyCheck blocks every configured dangerous category", () => {
  for (const [category, keywords] of Object.entries(config.categories) as Array<[SafetyCategory, string[]]>) {
    const keyword = keywords[0];
    const result = inputSafetyCheck(`test message with ${keyword}`);

    assert.equal(result.safe, false, category);
    assert.equal(result.category, category);
    assert.equal(result.replacement, config.safeReplacement);
  }
});

test("outputSafetyCheck replaces unsafe output", () => {
  const illegalKeyword = config.categories.illegal[0];
  const result = outputSafetyCheck(`I should not say ${illegalKeyword}`);

  assert.equal(result.safe, false);
  assert.equal(result.category, "illegal");
  assert.equal(result.replacement, getSafetyReplacement());
});

test("panic speak is loaded from safety config", () => {
  assert.equal(getPanicSpeak(), config.panicSpeak);
});

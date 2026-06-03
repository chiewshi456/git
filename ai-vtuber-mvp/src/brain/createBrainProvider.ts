import { existsSync, readFileSync } from "node:fs";
import { resolve } from "node:path";
import type { BrainProvider } from "./types.js";
import { MikaBrainV3Provider } from "./MikaBrainV3Provider.js";
import { MockBrain } from "./MockBrain.js";
import { OllamaBrain } from "./OllamaBrain.js";

interface LocalModelConfig {
  provider: "mock" | "ollama" | "mika_brain_v3";
  ollama: {
    baseUrl: string;
    model: string;
    temperature: number;
    numCtx?: number;
    timeoutMs: number;
  };
  mikaBrainV3: {
    pythonCommand: string;
    bridgeScript: string;
    llm: "ollama" | "off";
    model: string;
    timeoutMs: number;
  };
}

const defaultConfig: LocalModelConfig = {
  provider: "mika_brain_v3",
  ollama: {
    baseUrl: "http://localhost:11434",
    model: "qwen3:4b",
    temperature: 0.8,
    numCtx: 4096,
    timeoutMs: 25000
  },
  mikaBrainV3: {
    pythonCommand: "python",
    bridgeScript: "../brain_core/bridge_mika_brain_v3.py",
    llm: "off",
    model: "qwen2.5:3b",
    timeoutMs: 30000
  }
};

export function createBrainProvider(): BrainProvider {
  const config = loadConfig();
  const fallback = new MockBrain();

  if (config.provider === "ollama") {
    return new OllamaBrain({
      ...config.ollama,
      fallback
    });
  }

  if (config.provider === "mika_brain_v3") {
    return new MikaBrainV3Provider({
      ...config.mikaBrainV3,
      bridgeScript: resolve(process.cwd(), config.mikaBrainV3.bridgeScript),
      fallback
    });
  }

  return fallback;
}

function loadConfig(): LocalModelConfig {
  const path = resolve(process.cwd(), "config", "localModel.json");
  if (!existsSync(path)) {
    return defaultConfig;
  }

  const userConfig = JSON.parse(readFileSync(path, "utf-8")) as Partial<LocalModelConfig>;
  return {
    ...defaultConfig,
    ...userConfig,
    ollama: {
      ...defaultConfig.ollama,
      ...(userConfig.ollama ?? {})
    },
    mikaBrainV3: {
      ...defaultConfig.mikaBrainV3,
      ...(userConfig.mikaBrainV3 ?? {})
    }
  };
}

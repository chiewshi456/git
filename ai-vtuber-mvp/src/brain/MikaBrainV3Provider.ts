import { spawn } from "node:child_process";
import { dirname, resolve } from "node:path";
import { MockBrain } from "./MockBrain.js";
import type { BrainInput, BrainOutput, BrainProvider, Emotion, Gesture, ObsAction } from "./types.js";

export interface MikaBrainV3Options {
  pythonCommand: string;
  bridgeScript: string;
  llm: "ollama" | "off";
  model: string;
  timeoutMs: number;
  fallback?: BrainProvider;
}

interface MikaBridgeResponse {
  ok?: boolean;
  reply?: string;
  intent?: string;
  route?: string;
  topic?: string;
  model?: string;
  memorySummary?: string;
  error?: string;
}

export class MikaBrainV3Provider implements BrainProvider {
  private readonly fallback: BrainProvider;

  constructor(private readonly options: MikaBrainV3Options) {
    this.fallback = options.fallback ?? new MockBrain();
  }

  getInfo() {
    return {
      provider: "mika_brain_v3" as const,
      mode: "local_brain" as const,
      model: this.options.model,
      pythonCommand: this.options.pythonCommand,
      llm: this.options.llm,
      timeoutMs: this.options.timeoutMs
    };
  }

  generate(input: BrainInput): BrainOutput {
    throw new Error("Use generateAsync for MikaBrainV3Provider.");
  }

  async generateAsync(input: BrainInput): Promise<BrainOutput> {
    try {
      const response = await this.callBridge(input);
      if (!response.ok || !response.reply) {
        throw new Error(response.error || "empty Mika bridge response");
      }
      return this.toBrainOutput(input, response);
    } catch (error) {
      const fallbackOutput = this.fallback.generate(input);
      return {
        ...fallbackOutput,
        decisionReason: `Mika Brain v3 bridge unavailable, used MockBrain fallback. ${String(error)}`
      };
    }
  }

  private callBridge(input: BrainInput): Promise<MikaBridgeResponse> {
    return new Promise((resolvePromise, reject) => {
      const child = spawn(
        this.options.pythonCommand,
        [
          this.options.bridgeScript,
          "--llm",
          this.options.llm,
          "--model",
          this.options.model
        ],
        {
          cwd: dirname(this.options.bridgeScript),
          env: {
            ...process.env,
            PYTHONIOENCODING: "utf-8"
          },
          stdio: ["pipe", "pipe", "pipe"]
        }
      );

      let stdout = "";
      let stderr = "";
      let settled = false;
      const timer = setTimeout(() => {
        settled = true;
        child.kill();
        reject(new Error(`Mika bridge timed out after ${this.options.timeoutMs}ms`));
      }, this.options.timeoutMs);

      child.stdout.setEncoding("utf-8");
      child.stderr.setEncoding("utf-8");
      child.stdout.on("data", (chunk) => {
        stdout += chunk;
      });
      child.stderr.on("data", (chunk) => {
        stderr += chunk;
      });
      child.on("error", (error) => {
        if (settled) {
          return;
        }
        settled = true;
        clearTimeout(timer);
        reject(error);
      });
      child.on("close", (code) => {
        if (settled) {
          return;
        }
        settled = true;
        clearTimeout(timer);
        try {
          const response = JSON.parse(stdout.trim()) as MikaBridgeResponse;
          if (code !== 0 && !response.ok) {
            reject(new Error(response.error || stderr.trim() || `exit ${code}`));
            return;
          }
          resolvePromise(response);
        } catch (error) {
          reject(new Error(`invalid Mika bridge output: ${String(error)} ${stderr.trim()}`));
        }
      });

      child.stdin.end(
        JSON.stringify({
          text: input.selectedMessage.text,
          selectedMessage: input.selectedMessage,
          recentMessages: input.recentMessages.slice(0, 8),
          streamMemory: input.streamMemory,
          streamState: input.streamState
        })
      );
    });
  }

  private toBrainOutput(input: BrainInput, response: MikaBridgeResponse): BrainOutput {
    const safety = response.intent?.startsWith("safety_") ? "blocked" : "safe";
    return {
      replyTo: input.selectedMessage.id,
      speak: String(response.reply || "").slice(0, 180),
      emotion: this.emotionFor(response.intent),
      gesture: this.gestureFor(response.intent),
      obsAction: this.obsActionFor(response.intent),
      safety,
      decisionReason: [
        `Mika Brain v3 route=${response.route || "unknown"}`,
        `intent=${response.intent || "unknown"}`,
        `model=${response.model || "unknown"}`,
        response.memorySummary ? `memory=${response.memorySummary}` : ""
      ]
        .filter(Boolean)
        .join("; ")
    };
  }

  private emotionFor(intent?: string): Emotion {
    if (!intent) {
      return "neutral";
    }
    if (intent.startsWith("safety_")) {
      return "awkward";
    }
    if (intent.includes("feedback") || intent.includes("correction")) {
      return "serious";
    }
    if (intent.includes("teasing")) {
      return "teasing";
    }
    if (intent.includes("greeting") || intent.includes("remember")) {
      return "happy";
    }
    if (intent.includes("identity") || intent.includes("memory")) {
      return "confused";
    }
    return "neutral";
  }

  private gestureFor(intent?: string): Gesture {
    if (!intent) {
      return "none";
    }
    if (intent.startsWith("safety_")) {
      return "shake_head";
    }
    if (intent.includes("greeting")) {
      return "wave";
    }
    if (intent.includes("remember") || intent.includes("feedback") || intent.includes("correction")) {
      return "nod";
    }
    if (intent.includes("identity") || intent.includes("memory")) {
      return "tilt_head";
    }
    return "none";
  }

  private obsActionFor(intent?: string): ObsAction {
    if (intent?.startsWith("safety_")) {
      return "show_safe_skip";
    }
    return "highlight_chat";
  }
}

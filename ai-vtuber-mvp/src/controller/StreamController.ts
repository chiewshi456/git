import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { MockBrain } from "../brain/MockBrain.js";
import type { BrainOutput, BrainProvider, BrainProviderInfo, Persona } from "../brain/types.js";
import { MessageSelector } from "../chat/MessageSelector.js";
import { MockChatSource } from "../chat/MockChatSource.js";
import type { ChatMessage, MessageSelection } from "../chat/types.js";
import { MemoryModule } from "../memory/MemoryModule.js";
import { getPanicSpeak, getSafetyReplacement, inputSafetyCheck, outputSafetyCheck } from "../safety/SafetyModule.js";
import type { SafetyLog, SafetyResult } from "../safety/safetyTypes.js";
import { createId } from "../utils/ids.js";
import { log } from "../utils/logger.js";
import type { StreamState } from "./StreamState.js";

type DashboardPush = (snapshot: DashboardSnapshot) => void;

export interface StreamControllerOptions {
  source?: MockChatSource;
  selector?: MessageSelector;
  brain?: BrainProvider;
  memory?: MemoryModule;
  personaPath?: string;
  autoGenerateMockChat?: boolean;
}

export interface DashboardSnapshot {
  state: StreamState;
  running: boolean;
  chatMode: "manual" | "mock_auto";
  recentMessages: ChatMessage[];
  selectedMessage: ChatMessage | null;
  selection: MessageSelection;
  brain: BrainProviderInfo;
  output: BrainOutput | null;
  safetyLogs: SafetyLog[];
  memoryLogs: ReturnType<MemoryModule["getLogs"]>;
  decisionReason: string;
}

export class StreamController {
  private readonly persona: Persona;
  private readonly source: MockChatSource;
  private readonly selector: MessageSelector;
  private readonly brain: BrainProvider;
  private readonly memory: MemoryModule;
  private readonly autoGenerateMockChat: boolean;
  private push: DashboardPush | null = null;
  private state: StreamState = "idle";
  private running = false;
  private processing = false;
  private processAgain = false;
  private pendingReplyMessageId: string | null = null;
  private currentTopic: string | null = null;
  private recentMessages: ChatMessage[] = [];
  private safeMessages: ChatMessage[] = [];
  private safetyLogs: SafetyLog[] = [];
  private selection: MessageSelection = {
    selectedMessage: null,
    score: 0,
    reasons: ["尚未开始"]
  };
  private output: BrainOutput | null = null;

  constructor(options: StreamControllerOptions = {}) {
    this.persona = JSON.parse(
      readFileSync(options.personaPath ?? resolve(process.cwd(), "config", "persona.json"), "utf-8")
    ) as Persona;
    this.source = options.source ?? new MockChatSource();
    this.selector = options.selector ?? new MessageSelector();
    this.brain = options.brain ?? new MockBrain();
    this.memory = options.memory ?? new MemoryModule();
    this.autoGenerateMockChat = options.autoGenerateMockChat ?? false;
    this.memory.loadMemory();
    this.source.onMessage((message) => this.handleMessage(message));
  }

  setDashboardPush(push: DashboardPush): void {
    this.push = push;
    this.broadcast();
  }

  start(): void {
    this.running = true;
    this.state = "chatting";
    if (this.autoGenerateMockChat) {
      this.source.start();
    }
    this.memory.writeMemory({
      type: "stream_event",
      content: this.autoGenerateMockChat ? "直播大脑开始运行" : "手动聊天模式已开启"
    });
    this.broadcast();
  }

  pause(): void {
    this.running = false;
    this.processAgain = false;
    this.state = "paused";
    this.source.pause();
    this.broadcast();
  }

  resume(): void {
    if (this.state === "panic") {
      return;
    }
    this.running = true;
    this.state = "chatting";
    if (this.autoGenerateMockChat) {
      this.source.start();
    }
    this.broadcast();
  }

  panic(): void {
    this.running = false;
    this.processAgain = false;
    this.state = "panic";
    this.source.pause();
    this.output = this.panicOutput();
    this.memory.recordReply(this.output);
    this.broadcast();
  }

  clearContext(): void {
    this.currentTopic = null;
    this.processAgain = false;
    this.pendingReplyMessageId = null;
    this.recentMessages = [];
    this.safeMessages = [];
    this.safetyLogs = [];
    this.selection = {
      selectedMessage: null,
      score: 0,
      reasons: ["上下文已清空"]
    };
    this.output = null;
    this.memory.clearContext();
    if (this.state !== "panic" && !this.running) {
      this.state = "idle";
    }
    this.broadcast();
  }

  sendTestMessage(text: string): ChatMessage {
    return this.source.sendTestMessage(text);
  }

  getSnapshot(): DashboardSnapshot {
    return {
      state: this.state,
      running: this.running,
      chatMode: this.autoGenerateMockChat ? "mock_auto" : "manual",
      recentMessages: this.recentMessages.slice(0, 30),
      selectedMessage: this.selection.selectedMessage,
      selection: this.selection,
      brain: this.brain.getInfo?.() ?? {
        provider: "mock",
        mode: "mock",
        model: this.brain.constructor.name || "UnknownBrain"
      },
      output: this.output,
      safetyLogs: this.safetyLogs.slice(0, 40),
      memoryLogs: this.memory.getLogs(),
      decisionReason: this.output?.decisionReason ?? ""
    };
  }

  private handleMessage(message: ChatMessage): void {
    this.recentMessages.unshift(message);
    this.recentMessages = this.recentMessages.slice(0, 50);
    this.memory.recordUserSeen(message.userId, message.username);

    if (this.state === "panic") {
      this.output = this.panicOutput();
      this.memory.recordReply(this.output);
      this.broadcast();
      return;
    }

    const inputResult = inputSafetyCheck(message.text);
    this.addSafetyLog("input", message.text, inputResult);

    if (!inputResult.safe) {
      this.state = "safety_skip";
      this.selection = {
        selectedMessage: null,
        score: 0,
        reasons: [`危险弹幕未进入 Brain：${inputResult.category ?? "unknown"}`]
      };
      this.memory.writeMemory({
        type: "risk_note",
        userId: message.userId,
        content: `${inputResult.category ?? "unknown"}：${message.text}`
      });
      this.output = {
        replyTo: message.id,
        speak: inputResult.replacement ?? getSafetyReplacement(),
        emotion: "awkward",
        gesture: "shake_head",
        obsAction: "show_safe_skip",
        safety: "blocked",
        decisionReason: `inputSafetyCheck 阻止弹幕进入 Brain：${inputResult.reason ?? "未说明"}`
      };
      this.memory.recordReply(this.output);
      this.broadcast();
      return;
    }

    this.safeMessages.unshift(message);
    this.safeMessages = this.safeMessages.slice(0, 30);

    if (!this.running || this.state === "paused") {
      this.broadcast();
      return;
    }

    this.processSafeMessages(this.autoGenerateMockChat ? undefined : message.id);
  }

  private processSafeMessages(replyMessageId?: string): void {
    if (replyMessageId) {
      this.pendingReplyMessageId = replyMessageId;
    }

    if (this.processing) {
      this.processAgain = true;
      return;
    }

    const nextReplyMessageId = this.pendingReplyMessageId;
    this.pendingReplyMessageId = null;
    void this.processSafeMessagesAsync(nextReplyMessageId);
  }

  private async processSafeMessagesAsync(replyMessageId: string | null): Promise<void> {
    this.processing = true;

    try {
      this.state = "thinking";
      this.broadcast();

      const directReplyMessage = replyMessageId
        ? this.safeMessages.find((message) => message.id === replyMessageId) ?? null
        : null;
      this.selection = directReplyMessage
        ? {
            selectedMessage: directReplyMessage,
            score: 100,
            reasons: ["手动聊天模式：优先回复你刚发送的消息"]
          }
        : this.selector.select(
            this.safeMessages,
            (userId) => this.memory.getUserMemory(userId),
            this.currentTopic
          );

      const selectedMessage = this.selection.selectedMessage;
      if (!selectedMessage) {
        this.state = "chatting";
        this.broadcast();
        return;
      }

      const userMemory = this.memory.getUserMemory(selectedMessage.userId);
      const brainInput = {
        persona: this.persona,
        selectedMessage,
        recentMessages: this.safeMessages.slice(0, 10),
        userMemory,
        streamMemory: this.memory.summarizeRecentMemory(),
        streamState: this.state
      };
      const brainOutput = this.brain.generateAsync
        ? await this.brain.generateAsync(brainInput)
        : this.brain.generate(brainInput);

      if (this.isPanicState()) {
        return;
      }

      const outputResult = outputSafetyCheck(brainOutput.speak);
      this.addSafetyLog("output", brainOutput.speak, outputResult);

      if (!outputResult.safe) {
        brainOutput.speak = outputResult.replacement ?? getSafetyReplacement();
        brainOutput.safety = "blocked";
        brainOutput.emotion = "awkward";
        brainOutput.gesture = "shake_head";
        brainOutput.obsAction = "show_safe_skip";
        brainOutput.decisionReason = `outputSafetyCheck 替换危险输出：${outputResult.reason ?? "未说明"}`;
      }

      this.output = brainOutput;
      this.currentTopic = this.inferTopic(selectedMessage.text);

      if (brainOutput.memoryWrite) {
        this.memory.writeMemory(brainOutput.memoryWrite);
      }
      this.memory.recordReply(brainOutput);

      this.state = "speaking";
      this.broadcast();

      setTimeout(() => {
        if (this.state === "speaking" && this.running) {
          this.state = "chatting";
          this.broadcast();
        }
      }, 1100);

      log("info", "Brain reply generated", {
        selectedMessage: selectedMessage.text,
        speak: brainOutput.speak
      });
    } finally {
      this.processing = false;

      if (this.processAgain && this.running && this.state !== "panic" && this.state !== "paused") {
        this.processAgain = false;
        const nextReplyMessageId = this.pendingReplyMessageId;
        this.pendingReplyMessageId = null;
        setTimeout(() => this.processSafeMessages(nextReplyMessageId ?? undefined), 1200);
      } else {
        this.processAgain = false;
      }
    }
  }

  private addSafetyLog(direction: SafetyLog["direction"], text: string, result: SafetyResult): void {
    this.safetyLogs.unshift({
      id: createId("safety"),
      timestamp: Date.now(),
      direction,
      text,
      result
    });
    this.safetyLogs = this.safetyLogs.slice(0, 60);
  }

  private isPanicState(): boolean {
    return this.state === "panic";
  }

  private inferTopic(text: string): string | null {
    if (/AI|ai|人工智能|机器人/.test(text)) {
      return "AI";
    }
    if (/加班|早八|工作|CPU|cpu/.test(text)) {
      return "CPU";
    }
    if (/礼物|电池|SC|sc/.test(text)) {
      return "礼物";
    }
    return null;
  }

  private panicOutput(): BrainOutput {
    return {
      replyTo: null,
      speak: getPanicSpeak(),
      emotion: "awkward",
      gesture: "panic",
      obsAction: "switch_idle",
      safety: "blocked",
      decisionReason: "Panic Mode 已开启，跳过 Brain，只输出固定安全话术。"
    };
  }

  private broadcast(): void {
    this.push?.(this.getSnapshot());
  }
}

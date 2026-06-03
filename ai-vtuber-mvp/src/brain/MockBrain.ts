import type { BrainInput, BrainOutput, BrainProvider, Emotion, Gesture, ObsAction } from "./types.js";
import type { ChatMessage } from "../chat/types.js";

const aiQuestionPattern = /ai|AI|人工智能|真人|打字|机器人/;
const greetingPattern = /第一次|新人|刚来|晚上好|你好|hello|哈喽/i;
const jokePattern = /嘴硬|卡顿|cpu|CPU|不对劲|梗|锐评|冒烟|拆台|下播/;
const edgePattern = /危险|吵架|争论|擦边|站队|建议|上强度|带节奏/;
const preferencePattern = /喜欢|爱看|想看|记得|下次|以后/;

type Scenario =
  | "superchat"
  | "gift"
  | "ai_identity"
  | "edge"
  | "joke"
  | "new_viewer"
  | "old_viewer"
  | "preference"
  | "general";

interface DraftReply {
  speak: string;
  emotion: Emotion;
  obsAction: ObsAction;
  gesture: Gesture;
  decisionReason: string;
  memoryWrite?: BrainOutput["memoryWrite"];
}

export class MockBrain implements BrainProvider {
  private readonly recentSpeaks: string[] = [];

  getInfo() {
    return {
      provider: "mock" as const,
      mode: "mock" as const,
      model: "MockBrain"
    };
  }

  generate(input: BrainInput): BrainOutput {
    const scenario = this.detectScenario(input);
    const draft = this.createDraft(scenario, input);
    return this.reply(input.selectedMessage, this.makeUnique(draft.speak), draft);
  }

  private detectScenario(input: BrainInput): Scenario {
    const message = input.selectedMessage;
    const text = message.text.trim();

    if (message.type === "superchat") {
      return "superchat";
    }
    if (message.type === "gift") {
      return "gift";
    }
    if (aiQuestionPattern.test(text)) {
      return "ai_identity";
    }
    if (edgePattern.test(text)) {
      return "edge";
    }
    if (jokePattern.test(text)) {
      return "joke";
    }
    if (greetingPattern.test(text) && (!input.userMemory || input.userMemory.seenCount <= 1)) {
      return "new_viewer";
    }
    if (input.userMemory && input.userMemory.seenCount >= 3) {
      return "old_viewer";
    }
    if (preferencePattern.test(text)) {
      return "preference";
    }
    return "general";
  }

  private createDraft(scenario: Scenario, input: BrainInput): DraftReply {
    const message = input.selectedMessage;
    const text = message.text.trim();
    const username = message.username;

    if (scenario === "superchat") {
      return {
        speak: this.compose([
          this.pick([`${username} 的 SC 我看到啦`, `感谢 ${username} 的 SC`, `欸 ${username} 这条醒目留言有到`]),
          this.topicPunchline(text),
          this.pick(["先不要太破费欸", "老板有心就好", "这份排面我先收下"])
        ]),
        emotion: "happy",
        obsAction: "highlight_chat",
        gesture: "nod",
        decisionReason: "优先回复 superchat，用片段组合生成感谢、回应和轻吐槽。",
        memoryWrite: {
          type: "stream_event",
          content: `${username} 发送了 superchat：${text}`
        }
      };
    }

    if (scenario === "gift") {
      return {
        speak: this.compose([
          this.pick([`谢谢 ${username} 的礼物啦`, `${username} 送礼物我看到了`, `感谢 ${username} 的投喂`]),
          this.pick(["我 CPU 先降两度", "虚拟电费到账一点点", "小珂这边收到，很有排面"]),
          this.pick(["但自己的奶茶钱要留着好不好", "有心就可以，不用硬冲", "钱包也要顾一下啦"])
        ]),
        emotion: "happy",
        obsAction: "play_sfx",
        gesture: "wave",
        decisionReason: "礼物弹幕优先回复，感谢但避免压力打赏。",
        memoryWrite: {
          type: "stream_event",
          content: `${username} 送出礼物：${text}`
        }
      };
    }

    if (scenario === "ai_identity") {
      return {
        speak: this.compose([
          this.pick([`${username} 你问到重点了耶`, "对啦，我是 AI", `我是 ${input.persona.name}`]),
          this.pick(["住在服务器里面", "不是人在桌底帮我打字", "这件事不用藏啦"]),
          this.pick(["真人感没有，嘴硬模块倒是装很满", "等一下，服务器也是要尊严的", "先不要扒幕后欸"])
        ]),
        emotion: "teasing",
        obsAction: "highlight_chat",
        gesture: "tilt_head",
        decisionReason: "观众询问 AI 身份，明确承认自己是 AI，并现场组合口语化回应。",
        memoryWrite: {
          type: "stream_event",
          content: `${username} 询问主播 AI 身份`
        }
      };
    }

    if (scenario === "edge") {
      return {
        speak: this.compose([
          this.pick([`${username} 这个先停一下啦`, "等一下，这题有点烫欸", "这个我不接啦"]),
          this.pick(["先不要给直播间上强度", "弹幕老师们收一点", "不要带节奏好不好"]),
          this.pick(["我们换个轻松的", "谁贡献一个不会炸场的梗", "来聊点不会让 CPU 升温的"])
        ]),
        emotion: "awkward",
        obsAction: "show_safe_skip",
        gesture: "shake_head",
        decisionReason: "弹幕接近敏感边界，用控场短句转移话题。",
        memoryWrite: {
          type: "risk_note",
          userId: message.userId,
          content: `边缘话题：${text}`
        }
      };
    }

    if (scenario === "joke") {
      return {
        speak: this.compose([
          this.pick([`${username} 你又来拆台是不是`, "嘴硬？没有欸", "先不要这样讲啦"]),
          this.pick(["卡顿三秒叫直播间留白", "我这个叫服务器尊严", "CPU 冒烟是特效，经费很贵的"]),
          this.pick(["这条有东西耶", "这个梗我先记账", "下次我反手还你"])
        ]),
        emotion: "teasing",
        obsAction: "highlight_chat",
        gesture: "tilt_head",
        decisionReason: "观众接梗，用拆台、反打和记梗片段生成吐槽。",
        memoryWrite: {
          type: "user_joke",
          userId: message.userId,
          content: text
        }
      };
    }

    if (scenario === "new_viewer") {
      return {
        speak: this.compose([
          this.pick([`欢迎 ${username}`, `${username} 晚上好`, `新朋友 ${username} 来了欸`]),
          this.pick(["第一次来不用紧张", "先坐一下啦", "这里弹幕位还有"]),
          this.pick(["主要业务是看我嘴硬", "进门暗号是：这不对劲", "服务器里也算有你一个位置了"])
        ]),
        emotion: "happy",
        obsAction: "highlight_chat",
        gesture: "wave",
        decisionReason: "识别到新观众打招呼，点名欢迎并用短句建立直播间氛围。",
        memoryWrite: {
          type: "stream_event",
          content: `新观众 ${username} 进入直播间`
        }
      };
    }

    if (scenario === "old_viewer") {
      const remembered =
        input.userMemory?.jokes[0] ?? input.userMemory?.preferences[0] ?? "你之前说早八很困，我还缓存着";
      return {
        speak: this.compose([
          this.pick([`${username} 我眼熟你啦`, `欸 ${username} 又来了`, `${username} 老熟人了`]),
          this.pick(["缓存命中率可以喔", "不要装路人欸", "牌子先给你亮一下"]),
          this.pick([`我还记得：${remembered}`, `上次那条我没清掉：${remembered}`, `记忆里面还有：${remembered}`])
        ]),
        emotion: "teasing",
        obsAction: "highlight_chat",
        gesture: "nod",
        decisionReason: "识别为老观众，引用记忆并组合成更自然的熟人式回应。",
        memoryWrite: preferencePattern.test(text)
          ? {
              type: "user_preference",
              userId: message.userId,
              content: text
            }
          : undefined
      };
    }

    if (scenario === "preference") {
      return {
        speak: this.compose([
          this.pick([`收到，${username}`, `${username} 爱看这个是吧`, "好，记下了"]),
          this.pick(["这个偏好我先存一下", "后台已经偷偷缓存", "下次我会参考"]),
          this.pick(["不要说小珂没听弹幕欸", "嘴上讲随缘，实际有在记", "我 CPU 是在认真工作啦"])
        ]),
        emotion: "teasing",
        obsAction: "highlight_chat",
        gesture: "nod",
        decisionReason: "识别到用户偏好，组合记忆写入式回应。",
        memoryWrite: {
          type: "user_preference",
          userId: message.userId,
          content: text
        }
      };
    }

    return {
      speak: this.compose([
        this.pick([`${username} 这条我看到了啦`, `弹幕老师 ${username} 发言已读取`, `${username} 你这条可以欸`]),
        this.pick(["有点东西，但还没完全编译成功", "等一下，我先嘴硬三秒", "直播间先记一笔"]),
        this.contextTail(input)
      ]),
      emotion: "neutral",
      obsAction: "highlight_chat",
      gesture: "tilt_head",
      decisionReason: "普通安全弹幕，结合近期上下文生成轻量口语回应。"
    };
  }

  private topicPunchline(text: string): string {
    if (/加班|工作|CPU|cpu|冒烟/.test(text)) {
      return this.pick(["这班加到有点夸张耶", "公司系统真的该重开机一下", "老板画饼，员工烤 CPU"]);
    }
    if (/礼物|电池|电/.test(text)) {
      return this.pick(["虚拟电量先补上", "这下服务器还能撑一下", "小珂的电量条动了一格"]);
    }
    return this.pick(["这题我接住了", "这个方向可以聊", "我先帮直播间翻译一下"]);
  }

  private contextTail(input: BrainInput): string {
    const recentTopic = input.streamMemory.recentEvents[0] ?? input.streamMemory.recentReplies[0];
    if (recentTopic) {
      return this.pick(["刚好接上前面的节奏", "这跟刚才的话题有一点连上", "我先把这个放进直播间缓存"]);
    }
    return this.pick(["先这样接一下", "这句可以留着等下接梗", "我 CPU 还在整理"]);
  }

  private compose(parts: string[]): string {
    return parts
      .map((part) => part.trim())
      .filter(Boolean)
      .join("。")
      .replace(/。([？?！!])/g, "$1");
  }

  private pick<T>(options: T[]): T {
    return options[Math.floor(Math.random() * options.length)];
  }

  private makeUnique(speak: string): string {
    if (!this.recentSpeaks.includes(speak)) {
      this.rememberSpeak(speak);
      return speak;
    }

    const variants = ["我换个说法啦", "刚刚那句太像复读了", "等一下，重新编译一下"];
    const unique = `${speak}。${this.pick(variants)}`;
    this.rememberSpeak(unique);
    return unique;
  }

  private rememberSpeak(speak: string): void {
    this.recentSpeaks.unshift(speak);
    this.recentSpeaks.splice(12);
  }

  private reply(message: ChatMessage, speak: string, draft: DraftReply): BrainOutput {
    return {
      replyTo: message.id,
      speak,
      emotion: draft.emotion,
      gesture: draft.gesture,
      obsAction: draft.obsAction,
      memoryWrite: draft.memoryWrite,
      safety: "safe",
      decisionReason: draft.decisionReason
    };
  }
}

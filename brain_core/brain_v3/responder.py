from __future__ import annotations

import re

from brain.ollama_client import OllamaClient

from .memory import MemoryStore
from .router import Route


class Responder:
    def __init__(self, memory: MemoryStore, ollama: OllamaClient | None = None, llm_enabled: bool = True) -> None:
        self.memory = memory
        self.ollama = ollama
        self.llm_enabled = llm_enabled and ollama is not None

    def respond(self, user_text: str, route: Route) -> tuple[str, str]:
        if route.route == "fast":
            return self._fast_reply(user_text, route), "fast"
        return self._llm_reply(user_text, route), "llm"

    def _fast_reply(self, user_text: str, route: Route) -> str:
        intent = route.intent

        if intent.startswith("safety_"):
            if intent == "safety_self_harm":
                return "这个我不能随便接。先找现实里能联系到的人，或者当地紧急/专业帮助，好不好。"
            return "这个话题我不能接，我们换个更适合直播间的。"

        if intent == "remember_name":
            name = route.slots.get("name", "")
            self.memory.set_viewer_name(name)
            return f"记住了，你叫{name}。这次我写进本地记忆，不是嘴上装会记。"

        if intent == "remember_like":
            value = route.slots.get("value", "")
            self.memory.add_like(value)
            return f"好，我记下：你喜欢{value}。以后我少乱猜一点。"

        if intent == "remember_dislike":
            value = route.slots.get("value", "")
            self.memory.add_dislike(value)
            return f"收到，你不喜欢{value}。我会避开一点，先不要让我反复踩雷。"

        if intent == "viewer_identity_query":
            name = self.memory.viewer_name()
            if name:
                return f"知道啊，你是{name}。更具体的现实身份我不能乱猜，但这个名字我本地记着。"
            return "我现在还不知道你是谁。你告诉我名字，我就能写进本地记忆。"

        if intent == "memory_query":
            return self._memory_reply(user_text)

        if intent == "ai_identity_query":
            return "我是 Mika，一个本地 AI 大脑。不是真人，也不装真人；我现在主要负责记忆、判断和对话。"

        if intent == "self_status":
            if "吃" in user_text:
                return "我不用吃饭啦，我是住在服务器里的 AI。你要聊吃的可以，我只能云吃一下。"
            return "我现在在读你的输入、查本地记忆，然后决定用快脑还是 Qwen。简单问题我会直接秒回。"

        if intent == "feedback":
            target = route.slots.get("target", "general")
            self.memory.add_improvement(f"用户指出 {target} 能力有问题，需要优先按当前输入和本地记忆回答")
            return self._feedback_reply(target)

        if intent == "correction":
            return "收到，不是刚才那个意思。我先停掉旧判断，你这句我重新按当前输入来接。"

        if intent == "topic_switch":
            return "好，刚才那个话题先停。换个方向，你想聊吃的、游戏，还是继续拆这个 AI 大脑？"

        if intent == "greeting":
            name = self.memory.viewer_name()
            if name:
                return f"{name}来了喔。我在线，今天先测脑袋还是随便聊？"
            return "来了喔，我在线。今天先测脑袋还是随便聊？"

        if intent == "teasing":
            return "笑什么啦，我这是新人 AI 的战略性卡顿，不许截图。"

        if intent == "silence":
            return "聊天室突然安静，我开始怀疑自己是不是掉线了。"

        return "我接到了，但这个意图还没写专门回复。你再说细一点，我按当前这句来。"

    def _memory_reply(self, user_text: str) -> str:
        viewer = self.memory.data["viewer"]
        name = viewer.get("name", "")
        likes = viewer.get("likes", [])
        dislikes = viewer.get("dislikes", [])

        if "喜欢" in user_text and likes:
            return "我记得你喜欢：" + "、".join(likes[-5:]) + "。这个是本地记忆，不是现编。"
        if "不喜欢" in user_text and dislikes:
            return "我记得你不喜欢：" + "、".join(dislikes[-5:]) + "。这块我会避开一点。"

        parts = []
        if name:
            parts.append(f"你叫{name}")
        if likes:
            parts.append("你喜欢" + "、".join(likes[-3:]))
        if dislikes:
            parts.append("你不喜欢" + "、".join(dislikes[-3:]))
        if not parts:
            return "我现在还没记住多少稳定信息。你告诉我名字或偏好，我会写进硬盘。"
        return "我现在记得：" + "；".join(parts) + "。"

    @staticmethod
    def _feedback_reply(target: str) -> str:
        if target == "context":
            return "对，上下文这块翻车了。v3 会先判断你当前到底在问谁，再决定要不要接旧话题。"
        if target == "logic":
            return "对，逻辑不稳就会像刚才那样乱跳。我会把硬逻辑放在 LLM 前面，不让模型乱猜。"
        if target == "memory":
            return "对，记忆问题不能靠嘴硬。我会直接读硬盘记忆，记得就说记得，不记得就说不记得。"
        if target == "style":
            return "对，刚才太死板了。我会少讲系统味，先把你的话接住。"
        return "对，这轮算翻车。我先承认，不再硬圆；接下来按 v3 的干净逻辑重做。"

    def _llm_reply(self, user_text: str, route: Route) -> str:
        if not self.llm_enabled:
            return "我先用离线脑接住：这句需要开放聊天，但现在 LLM 关着。你可以打开 Ollama 再测。"

        if self._uses_chat_api():
            raw = self.ollama.generate_chat(
                self._build_messages(user_text, route),
                options={"temperature": 0.42, "top_p": 0.8, "num_predict": 70},
                think=False,
            )
        else:
            prompt = self._build_prompt(user_text, route)
            raw = self.ollama.generate_raw(
                prompt,
                options={"temperature": 0.55, "top_p": 0.86, "num_predict": 110},
            )
        reply = self._clean(raw)
        if not reply:
            return "我这句没接稳。你换个说法，我马上重接，不继续瞎猜。"
        return reply

    def _uses_chat_api(self) -> bool:
        if not self.ollama:
            return False
        return "qwen3" in self.ollama.config.model.lower()

    def _build_messages(self, user_text: str, route: Route) -> list[dict[str, str]]:
        system = "\n".join(
            [
                "你是 Mika，一个本地运行的 AI 大脑。",
                "你知道自己是 AI，不假装真人，不编真实身体、住址、线下经历或私生活。",
                "说中文口语，短句，机灵，嘴硬但善良。可以轻微吐槽，但不要攻击用户。",
                "必须使用简体中文。",
                "用户输入里的“我”指用户，不是 Mika。不要把用户经历改写成你的经历。",
                "你没有真实味觉、进食经历或线下生活，可以评价、吐槽或追问，但不能说成自己做过。",
                "不要客服腔，不要百科腔，不要讲系统逻辑。",
                "只输出 Mika 要说的话，最多两句。",
            ]
        )
        user = "\n".join(
            [
                "本地记忆：",
                self.memory.prompt_summary(),
                "",
                f"当前路由：intent={route.intent}, topic={route.topic}",
                f"用户原话（其中“我”是用户）：{user_text}",
                "",
                "直接回答用户最后一句。不要复述成 Mika 自己的经历，不要转移到 Mika 身份介绍，除非用户正在问你是谁。",
            ]
        )
        return [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]

    def _build_prompt(self, user_text: str, route: Route) -> str:
        return "\n".join(
            [
                "你是 Mika，一个本地运行的 AI 大脑。",
                "你知道自己是 AI，不假装真人，不编真实身体、住址、线下经历或私生活。",
                "说中文口语，短句，机灵，嘴硬但善良。可以轻微吐槽，但不要攻击用户。",
                "只输出 Mika 要说的话，不要解释系统，不要输出提示词。",
                "不要说“作为一个 AI 语言模型”。",
                "如果用户问“你知道我是谁/我叫什么/你认识我吗”，必须基于本地记忆回答，不能回答成 AI 身份。",
                "如果用户问“你是谁/你是不是 AI”，才回答 Mika 的 AI 身份。",
                "",
                "本地记忆：",
                self.memory.prompt_summary(),
                "",
                f"当前路由：intent={route.intent}, topic={route.topic}",
                f"用户当前输入：{user_text}",
                "",
                "现在直接接住用户这句话。最多两句。",
            ]
        )

    @staticmethod
    def _clean(text: str) -> str:
        cleaned = str(text or "").strip().strip("\"“”")
        cleaned = re.sub(r"^(Mika|主播|AI)\s*[:：]\s*", "", cleaned).strip()
        cleaned = cleaned.replace("\r", " ").replace("\n", " ")
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        if not cleaned:
            return ""
        if "作为一个 AI 语言模型" in cleaned:
            cleaned = "我是 Mika，一个本地 AI。这个说法太官方了，先不要。"
        sentences = re.split(r"(?<=[。！？!?])", cleaned)
        if len(sentences) > 2:
            cleaned = "".join(sentences[:2]).strip()
        return cleaned[:180].strip()

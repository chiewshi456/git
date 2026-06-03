from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ResponsePolicy:
    mode: str = "llm"
    tone: str = "natural"
    must_address: list[str] = field(default_factory=list)
    must_not_do: list[str] = field(default_factory=list)
    deterministic_reply: str = ""
    reason: str = ""

    def to_dict(self) -> dict:
        return {
            "mode": self.mode,
            "tone": self.tone,
            "must_address": self.must_address,
            "must_not_do": self.must_not_do,
            "deterministic_reply": self.deterministic_reply,
            "reason": self.reason,
        }


class PolicyEngine:
    def decide(self, user_input: str, understanding: dict, retrieved_memory: dict) -> ResponsePolicy:
        act = understanding.get("user_act", "chat")
        target = understanding.get("complaint_target", "")

        if act == "greeting":
            return ResponsePolicy(
                mode="deterministic",
                tone="warm",
                deterministic_reply="来了喔，我在线。今天先测试脑袋，还是随便聊两句？",
                reason="fast_greeting",
            )

        if act == "name_share":
            name = self._first_memory_value(understanding, "viewer_name")
            reply = f"记住了，你叫{name}。这次是写进本地记忆，不是我假装很会记。" if name else "我收到你的名字了。等一下，我先把这个写进本地记忆。"
            return ResponsePolicy(
                mode="deterministic",
                tone="direct",
                deterministic_reply=reply,
                reason="fast_name_share",
            )

        if act == "preference_share":
            preference = self._first_memory_value(understanding, "viewer_preference")
            reply = f"好，我记一下：你喜欢{preference}。先不要过度测试我，我会紧张。" if preference else "好，我会把这个偏好记下来，之后回答时少乱猜一点。"
            return ResponsePolicy(
                mode="deterministic",
                tone="direct",
                deterministic_reply=reply,
                reason="fast_preference_share",
            )

        if act == "topic_switch" or understanding.get("wants_topic_switch"):
            return ResponsePolicy(
                mode="deterministic",
                tone="calm",
                deterministic_reply="好，刚才那个话题先停。我换个方向：聊吃的、游戏，还是你今天发生的事？",
                must_not_do=["不要继续旧话题"],
                reason="topic_switch",
            )

        if act in {"feedback", "correction"} or understanding.get("should_apologize"):
            reply = self._feedback_reply(target)
            return ResponsePolicy(
                mode="deterministic",
                tone="accountable",
                deterministic_reply=reply,
                must_address=["承认问题", "说明修正方向"],
                must_not_do=["不要反问用户是不是在测试", "不要继续旧话题"],
                reason=f"feedback:{target}",
            )

        if act == "self_status_query":
            if any(word in user_input for word in ("吃了吗", "吃饭了吗")):
                reply = "我不用吃饭，我是住在服务器里的 AI。你要聊吃的也可以，我不会装自己真的吃过。"
            else:
                reply = "我现在在读你的输入、查相关记忆、判断你的真实意图，然后决定用快脑还是本地模型回复。"
            return ResponsePolicy(
                mode="deterministic",
                tone="direct",
                deterministic_reply=reply,
                reason="self_status",
            )

        if any(word in user_input for word in ("你又知道", "你怎么知道", "你凭什么知道")):
            return ResponsePolicy(
                mode="deterministic",
                tone="direct",
                deterministic_reply="我不能真的知道你的想法，只能根据你刚才的话推断。刚才如果说太满，是我判断过头了。",
                must_not_do=["不要装作读心"],
                reason="overclaim_correction",
            )

        if act == "memory_query":
            reply = self._memory_query_reply(user_input, retrieved_memory)
            return ResponsePolicy(
                mode="deterministic",
                tone="direct",
                deterministic_reply=reply,
                must_address=["根据检索到的记忆回答，不知道就说不知道"],
                must_not_do=["不要编用户信息"],
                reason="fast_memory_query",
            )

        if act == "identity_query":
            return ResponsePolicy(
                mode="deterministic",
                tone="direct",
                deterministic_reply="对，我是 AI，不遮啦。我住在服务器里，没有真实身体，也不会假装真人。",
                reason="identity",
            )

        return ResponsePolicy(
            mode="llm",
            tone="natural",
            must_address=["接住用户当前这句话"],
            must_not_do=["不要无条件继承旧话题", "不要答非所问"],
            reason="general",
        )

    @staticmethod
    def _feedback_reply(target: str) -> str:
        if target == "context":
            return "对，刚才上下文接错了。我不该把旧话题硬粘到新问题上，之后会先判断你是不是已经换题。"
        if target == "logic":
            return "对，刚才逻辑不稳。我应该先判断你的真实意图，再决定要不要接旧话题。"
        if target == "memory":
            return "对，记忆这块刚才处理得差。我应该直接说我记得什么、不记得什么，而不是一直反问你。"
        if target == "reply_style":
            return "对，我刚才一直重复同一句，像卡住了。接下来我会先判断你的新输入，不再把换话题那句硬套上去。"
        return "对，刚才我接得不够准。我先承认这个问题，再把回复往你的真实意思上拉。"

    @staticmethod
    def _first_memory_value(understanding: dict, memory_type: str) -> str:
        candidates = understanding.get("stable_memory_candidates", [])
        if not isinstance(candidates, list):
            return ""
        for item in candidates:
            if not isinstance(item, dict):
                continue
            if item.get("type") == memory_type:
                return str(item.get("value", "")).strip()
        return ""

    @staticmethod
    def _memory_query_reply(user_input: str, retrieved_memory: dict) -> str:
        facts = retrieved_memory.get("facts", [])
        preferences = retrieved_memory.get("preferences", [])
        viewer_name = ""
        items = []
        for value in facts + preferences:
            text = str(value).strip()
            if not text:
                continue
            if text.startswith("用户名字="):
                viewer_name = text.split("=", 1)[1].strip()
            text = text.replace("用户名字=", "你叫")
            text = text.replace("喜欢=", "你喜欢")
            text = text.replace("不喜欢=", "你不喜欢")
            items.append(text)
        if not items:
            return "我现在没有稳定记住太多东西。你可以直接告诉我名字或偏好，我会写进本地记忆。"
        if viewer_name and any(word in user_input for word in ("是谁", "认识我", "知道我")):
            return f"知道啊，你是{viewer_name}。更具体的现实身份我不能乱猜，但本地记忆里这个名字是稳的。"
        return "我记得：" + "；".join(items[:3]) + "。先不要说我完全没记忆，好不好。"

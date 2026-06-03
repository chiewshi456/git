from __future__ import annotations


class ReplyCritic:
    BAD_OLD_TOPIC_MARKERS = ("测试记忆", "你又来问我记忆", "还是你想看看")

    def review(self, reply: str, user_input: str, understanding: dict, policy: dict) -> tuple[str, bool, str]:
        text = reply.strip()
        if not text:
            return "我刚才没接稳。你这句我重新理解一下。", True, "empty"

        if understanding.get("wants_topic_switch") and self._mentions_old_topic(text):
            return "好，旧话题先停。我换个方向，不继续刚才那个。", True, "ignored_topic_switch"

        if understanding.get("user_act") in {"feedback", "correction"}:
            if any(marker in text for marker in self.BAD_OLD_TOPIC_MARKERS):
                target = understanding.get("complaint_target", "")
                return self._feedback_repair(target), True, "bad_feedback_reply"
            if "测试" in text and "记忆" in text:
                return "对，我不该又往测试记忆上拐。你是在纠正我的理解问题，我先承认这个。", True, "kept_testing_frame"

        if any(word in user_input for word in ("你吃了吗", "你吃饭了吗")) and any(
            word in text for word in ("我吃", "刚吃", "还没吃")
        ):
            return "我不用吃饭，我是 AI。可以聊吃的，但我不会假装自己真的吃过。", True, "fake_body"

        if len(text) > 130:
            cut = text[:130].rstrip("，,、；; ")
            if cut and cut[-1] not in "。！？!?":
                cut += "。"
            return cut, True, "too_long"

        return text, False, ""

    def _mentions_old_topic(self, text: str) -> bool:
        return any(marker in text for marker in self.BAD_OLD_TOPIC_MARKERS)

    @staticmethod
    def _feedback_repair(target: str) -> str:
        if target == "context":
            return "对，你说的是上下文问题。我刚才没有先判断你是不是换了意思，这是我接错了。"
        if target == "logic":
            return "对，你说的是逻辑问题。我刚才没有先判断你的真实意图，就急着回了。"
        if target == "memory":
            return "对，你说的是记忆问题。我应该直接说明我记得什么，而不是一直反问。"
        return "对，刚才我接偏了。你是在纠正我，我应该先承认问题。"

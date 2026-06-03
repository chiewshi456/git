from __future__ import annotations

from typing import Any


class ReplyQualityGate:
    """Detect weak template replies and repair them before they reach output."""

    WEAK_SNIPPETS = (
        "我看到了",
        "这句弹幕我接住了",
        "这句消息我接住了",
        "你这个话题可以继续讲",
        "我在听，不是在发呆",
        "先拆小一点做",
        "我倾向于说是",
        "这个问题可以答",
        "我先用现在这个小脑袋回答一下",
    )

    def repair(self, reply: str, context: dict[str, Any]) -> tuple[str, bool, str]:
        dialogue = context.get("dialogue", {})
        user_input = str(context.get("user_input", ""))
        fast_reply = str(reply).strip()

        deterministic = self._deterministic_reply(user_input, dialogue)
        if deterministic:
            return deterministic, True, "deterministic_context"

        if dialogue.get("wants_topic_switch"):
            return self._repair_topic_switch(), True, "topic_switch"

        if dialogue.get("is_meta_complaint"):
            return self._repair_meta_complaint(dialogue), True, "meta_complaint"

        if dialogue.get("asks_reason") and dialogue.get("topic"):
            repaired = self._repair_reason(dialogue)
            if repaired:
                return repaired, True, "topic_reason"

        if dialogue.get("references_previous") or dialogue.get("wants_continuation"):
            repaired = self._repair_follow_up(user_input, dialogue)
            if repaired:
                return repaired, True, "follow_up_context"

        if dialogue.get("asks_opinion") and dialogue.get("topic"):
            repaired = self._repair_opinion(user_input, dialogue)
            if repaired:
                return repaired, True, "topic_opinion"

        if self._is_weak(fast_reply) and dialogue.get("topic"):
            repaired = self._repair_by_topic(user_input, dialogue)
            if repaired:
                return repaired, True, "weak_template"

        return fast_reply, False, ""

    def _deterministic_reply(
        self,
        user_input: str,
        dialogue: dict[str, Any],
    ) -> str:
        text = user_input.strip()
        if not text:
            return ""

        if any(marker in text for marker in ("你现在在干嘛", "你在干嘛", "你正在干嘛", "你做什么")):
            return "我现在在读你的输入、查上一轮上下文、更新记忆，然后决定要用快脑还是本地模型接话。"

        if any(marker in text for marker in ("你吃了吗", "你吃饭了吗", "吃了吗")):
            return "我不用吃饭啦，我是住在服务器里的 AI。你要是想换吃的这个话题，我可以陪你聊。"

        if any(marker in text for marker in ("你怎么知道", "你又知道", "你凭什么知道")):
            last_reply = str(dialogue.get("last_ai_reply", "")).strip()
            if "测试" in last_reply or "记忆" in last_reply:
                return "这句我确实说过头了。我只是看到你在问记忆，就误判成你在测试我，不该装得好像很确定。"
            return "我不能真的知道你的想法，只能根据你刚才说的话推断。刚才如果说太满，那是我判断过头了。"

        if "不是" in text and any(marker in text for marker in ("上下文", "逻辑", "记忆")):
            return "对，你是在纠正我，不是在继续旧话题。我应该先承认接错，再调整，不该继续往记忆测试上拐。"

        return ""

    @staticmethod
    def _repair_topic_switch() -> str:
        return "好，刚才那个话题先停。我换个轻一点的：聊吃的、游戏，还是你今天发生的事？"

    def _is_weak(self, reply: str) -> bool:
        if len(reply.strip()) < 10:
            return True
        return any(snippet in reply for snippet in self.WEAK_SNIPPETS)

    @staticmethod
    def _repair_meta_complaint(dialogue: dict[str, Any]) -> str:
        last_reply = str(dialogue.get("last_ai_reply", "")).strip()
        if last_reply:
            return "对，刚才那句接偏了。我把旧话题硬套到新问题上，应该先判断你是不是在纠正我。"
        return "对，现在还不够聪明。问题不只是口语，是上下文、自检和追问能力还要补，我会往这三块长。"

    @staticmethod
    def _repair_follow_up(user_input: str, dialogue: dict[str, Any]) -> str:
        last_user = str(dialogue.get("last_user_input", "")).strip()
        last_reply = str(dialogue.get("last_ai_reply", "")).strip()
        if not last_user and not last_reply:
            return ""

        if any(word in user_input for word in ("什么意思", "解释", "为什么")):
            return f"我刚才接得太跳了。你上一句是“{last_user[:24]}”，我应该先围着这个讲，不该直接丢模板。"
        if any(word in user_input for word in ("继续", "接着", "然后呢", "展开")):
            continued = ReplyQualityGate._continue_topic(dialogue)
            if continued:
                return continued
            topic = ReplyQualityGate._topic_label(dialogue.get("topic") or "这个话题")
            return f"好，继续接{topic}。我先不换话题，顺着你刚才那句往下说。"
        if any(word in user_input for word in ("这个", "那句", "刚才", "刚刚", "上一句")):
            return "我知道你在指刚才那轮。等一下，我先把上下文捡回来，不要又像失忆一样乱接。"
        return ""

    @staticmethod
    def _repair_reason(dialogue: dict[str, Any]) -> str:
        topic = dialogue.get("topic", "")
        if topic == "food":
            return "因为火锅不是那种需要装深沉的东西，热、香、能聊天，基本就赢一半了。"
        if topic == "game":
            return "因为游戏很容易把人的性格打出来。认真、嘴硬、破防，几分钟就藏不住。"
        if topic == "tech":
            return "因为技术问题最怕一句话糊过去。上下文不够，我就会像刚开机一样乱猜。"
        if topic == "work":
            return "因为你说累的时候，重点通常不是解决全世界，是先别让自己继续硬撑。"
        if topic == "brain":
            return "因为光有模板不算智能。能记住上一句、发现自己答偏、再改口，才像在对话。"
        return ""

    @staticmethod
    def _repair_opinion(user_input: str, dialogue: dict[str, Any]) -> str:
        topic = dialogue.get("topic", "")
        if topic == "food":
            return "我觉得可以，吃火锅这种事很难失败。重点是你吃辣锅还是清汤，这会暴露阵营。"
        if topic == "game":
            return "我觉得可以聊。游戏这东西一半是技术，一半是嘴硬，听起来很适合测试我。"
        if topic == "tech":
            return "我觉得要先看具体问题。只说代码有 bug 太宽了，把报错丢出来我比较能接住。"
        if topic == "work":
            return "我觉得你应该先把自己从工作模式里拔出来一点。累到还要解释，很亏。"
        return ""

    @staticmethod
    def _topic_label(topic: str) -> str:
        labels = {
            "food": "吃的",
            "work": "工作",
            "game": "游戏",
            "tech": "技术",
            "emotion": "情绪",
            "brain": "智能这块",
            "music": "音乐",
        }
        return labels.get(topic, topic)

    @staticmethod
    def _repair_by_topic(user_input: str, dialogue: dict[str, Any]) -> str:
        topic = dialogue.get("topic", "")
        if topic == "brain":
            return "你是在测试我的脑子，对吧。现在我能记偏好，但真正像对话还得靠上下文和自检。"
        if topic == "food":
            return "讲吃的我能接。你别只丢一个词，告诉我你吃了什么，我比较不会像模板机。"
        if topic == "work":
            return "工作话题我先认真接。你是累，还是被某件事卡住了？这两个方向不一样。"
        if topic == "tech":
            return "技术话题先给我一个具体点。报错、目标、你试过什么，三选一也行。"
        return ""

    @staticmethod
    def _continue_topic(dialogue: dict[str, Any]) -> str:
        topic = dialogue.get("topic", "")
        if topic == "food":
            return "继续讲火锅的话，锅底就是性格测试。清汤很稳，辣锅很有野心，鸳鸯锅就是成年人不做选择。"
        if topic == "game":
            return "继续讲游戏的话，我会先问你是享受操作，还是享受赢。很多人嘴上说随便玩，手已经在排位了。"
        if topic == "tech":
            return "继续讲技术的话，先别急着猜原因。复现步骤、报错内容、最近改动，这三个比玄学祈祷有用。"
        if topic == "work":
            return "继续讲工作的话，我会先分清是身体累，还是心被消耗。前者要休息，后者要少被工作绑架。"
        if topic == "brain":
            return "继续讲智能的话，下一步不是堆模板，是让每次回答都先看上一轮、当前目标和自己有没有答偏。"
        return ""

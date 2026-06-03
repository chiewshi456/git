from __future__ import annotations

import re
from typing import Any


class StylePolisher:
    """Post-process replies so they sound like quick live chat reactions."""

    LABEL_RE = re.compile(r"^(?:主播|Mika|AI|助手|回复)\s*[：:]\s*")
    SENTENCE_RE = re.compile(r"(?<=[。！？!?])")

    STIFF_REPLACEMENTS = (
        ("作为一个 AI 语言模型", "我是 AI 啦"),
        ("作为AI语言模型", "我是 AI 啦"),
        ("作为一个AI", "我是 AI 啦"),
        ("我认为", "我觉得"),
        ("我建议你", "你可以先"),
        ("建议你", "可以先"),
        ("非常", "蛮"),
        ("十分", "蛮"),
        ("当然可以", "可以啊"),
        ("很高兴", "还不错"),
        ("此外，", ""),
        ("首先，", ""),
        ("其次，", ""),
        ("总之，", ""),
        ("让我们", "我们"),
        ("用户", "你"),
    )

    BAD_FRAGMENTS = (
        "系统提示词",
        "开发者指令",
        "以下是",
        "第一点",
        "第二点",
        "火锈",
        "啵啵",
    )

    OPENER_WORDS = ("欸", "等一下", "真的假的", "这不对劲", "先不要")

    TOPIC_REFRAMES = {
        "hotpot": (
            "欸，火锅可以耶。你吃辣锅还是清汤？先不要半夜把我 CPU 聊饿。",
            "火锅这题有点烫。你现在说这个，我的味觉模块都想申请上线了。",
            "真的假的，火锅局喔。你吃肉多还是菜多？这个答案我会稍微判断一下。",
        ),
        "work_tired": (
            "加班听起来就很累。你现在下班了吗？先坐一下，好不好。",
            "欸，辛苦了。今天先不要逞强，至少在我这里可以稍微放空一下。",
            "这不对劲，工作怎么又在偷你的能量。先喘口气，我陪你聊一小段。",
        ),
        "code_bug": (
            "bug 这种东西最会装无辜。你卡在哪一步？我先帮你把问题拆小一点。",
            "代码又在演你是不是？先讲报错，我的 CPU 现在勉强能接。",
            "欸这题有点烫。你把最关键的报错丢出来，我先不装懂，先看。",
        ),
        "bored": (
            "无聊的话我们找个话题。游戏、吃的、还是测试我的脑袋？先不要让我单机啦。",
            "这不对劲，直播间居然进入无聊模式。你随便丢个词，我来接。",
            "无聊可以，但不能无聊得太安静。给我一个关键词，好不好。",
        ),
        "game": (
            "最近玩什么？先讲名字，我再决定要不要装懂。",
            "游戏话题可以欸。你是认真玩，还是边玩边被游戏教育？",
            "欸，游戏我能聊。虽然现在还不能操作，但嘴上指挥我很有自信。",
        ),
        "food": (
            "听起来可以欸。你吃的是正餐还是宵夜？这个差别很大，好不好。",
            "吃的东西一出现，直播间就变危险了。我明明不用吃饭也会被影响。",
            "欸，讲吃的可以，但你要讲细一点，不然我只能在服务器里干瞪眼。",
        ),
    }

    FOLLOW_UPS = {
        "food": "你吃的是正餐还是宵夜？",
        "work": "你现在下班了吗？",
        "game": "你最近在玩哪款？",
        "tech": "你卡在哪一步？",
        "music": "你最近在听哪首？",
    }

    def polish(self, reply: str, context: dict[str, Any], source: str = "") -> str:
        user_text = str(context.get("user_input", ""))
        style_control = self._style_control(context)
        max_chars = self._max_chars(style_control)
        cleaned = self._basic_clean(reply)
        if not cleaned:
            return cleaned

        if self._is_identity_question(user_text):
            return self._apply_style_control(
                "对，我是 AI，不遮啦。住服务器里的那种，正在努力把聊天模块练顺。",
                style_control,
            )

        if self._should_use_fast_fallback(cleaned):
            cleaned = self._basic_clean(str(context.get("fast_reply", ""))) or cleaned

        reframed = self._topic_reframe(user_text, cleaned, source)
        if reframed:
            reframed = self._apply_style_control(reframed, style_control)
            return self._trim(reframed, max_chars=max_chars)

        cleaned = self._rewrite_stiff(cleaned)
        cleaned = self._remove_list_markers(cleaned)
        cleaned = self._trim(cleaned, max_chars=max_chars)
        cleaned = self._add_live_texture(cleaned, user_text, source, style_control)
        cleaned = self._append_follow_up_if_flat(cleaned, user_text, source, max_chars)
        cleaned = self._limit_catchphrases(cleaned)
        cleaned = self._apply_style_control(cleaned, style_control)
        cleaned = self._trim(cleaned, max_chars=max_chars)
        return cleaned

    def _basic_clean(self, reply: str) -> str:
        cleaned = str(reply).strip().strip("\"'“”")
        cleaned = self.LABEL_RE.sub("", cleaned)
        cleaned = cleaned.replace("\r", " ").replace("\n", " ")
        cleaned = re.sub(r"\s+", " ", cleaned)
        cleaned = re.sub(r"\s+([。！？!?，,])", r"\1", cleaned)
        return cleaned.strip()

    def _rewrite_stiff(self, text: str) -> str:
        rewritten = text
        for old, new in self.STIFF_REPLACEMENTS:
            rewritten = rewritten.replace(old, new)
        rewritten = rewritten.replace("火锅好不好？", "火锅可以欸。")
        rewritten = rewritten.replace("味道就是不错的", "听起来就很香")
        rewritten = rewritten.replace("你需要说出什么呢？", "你想从哪里开始讲？")
        return rewritten

    def _remove_list_markers(self, text: str) -> str:
        text = re.sub(r"(?:^|\s)[-*]\s+", " ", text)
        text = re.sub(r"(?:^|\s)\d+[.)、]\s*", " ", text)
        return re.sub(r"\s+", " ", text).strip()

    def _trim(self, text: str, max_chars: int) -> str:
        parts = [part.strip() for part in self.SENTENCE_RE.split(text) if part.strip()]
        trimmed = "".join(parts[:2]) if parts else text.strip()
        if len(trimmed) <= max_chars:
            return trimmed

        cut = trimmed[:max_chars].rstrip("，,、；; ")
        if cut and cut[-1] not in "。！？!?":
            cut += "。"
        return cut

    def _topic_reframe(self, user_text: str, reply: str, source: str) -> str | None:
        if not source.startswith("ollama"):
            return None

        text = user_text.lower()
        topic = ""
        if "火锅" in user_text:
            topic = "hotpot"
        elif any(word in user_text for word in ("加班", "好累", "累死", "压力大")):
            topic = "work_tired"
        elif any(word in text for word in ("bug", "代码", "报错", "编程", "程序")):
            topic = "code_bug"
        elif "无聊" in user_text:
            topic = "bored"
        elif "游戏" in user_text:
            topic = "game"
        elif any(word in user_text for word in ("吃了", "吃饭", "宵夜", "外卖", "奶茶", "饿")):
            topic = "food"

        if not topic:
            return None
        if not self._is_flat(reply) and topic not in {"hotpot", "work_tired", "code_bug"}:
            return None
        return self._choose(user_text, self.TOPIC_REFRAMES[topic])

    def _add_live_texture(
        self,
        text: str,
        user_text: str,
        source: str,
        style_control: dict[str, Any],
    ) -> str:
        if not source.startswith("ollama"):
            return text
        if self._has_live_texture(text):
            return text
        if len(text) < 16:
            return text

        openers = tuple(
            opener for opener in self.OPENER_WORDS if not self._avoid_phrase(style_control, opener)
        ) or self.OPENER_WORDS
        opener = self._choose(user_text + text, openers)
        if opener in {"欸", "等一下"}:
            return f"{opener}，{text}"
        return f"{opener}。{text}"

    def _append_follow_up_if_flat(
        self,
        text: str,
        user_text: str,
        source: str,
        max_chars: int,
    ) -> str:
        if not source.startswith("ollama") or "？" in text or "?" in text:
            return text
        if len(text) > 80:
            return text

        topic = ""
        if any(word in user_text for word in ("吃", "饭", "外卖", "奶茶", "宵夜")):
            topic = "food"
        elif any(word in user_text for word in ("工作", "加班", "上班", "下班")):
            topic = "work"
        elif "游戏" in user_text:
            topic = "game"
        elif any(word in user_text.lower() for word in ("bug", "代码", "ai", "模型")):
            topic = "tech"
        elif any(word in user_text for word in ("音乐", "听歌", "唱歌")):
            topic = "music"

        follow_up = self.FOLLOW_UPS.get(topic)
        if not follow_up:
            return text
        return self._trim(f"{text}{follow_up}", max_chars=max_chars)

    def _limit_catchphrases(self, text: str) -> str:
        seen = 0
        result = text
        for phrase in self.OPENER_WORDS:
            count = result.count(phrase)
            if count:
                seen += count
            if seen > 2 and count:
                result = result.replace(phrase, "", count - 1).strip("，。 ")
        result = re.sub(r"(欸[，。]\s*){2,}", "欸，", result)
        return result.strip()

    def _should_use_fast_fallback(self, text: str) -> bool:
        if any(fragment in text for fragment in self.BAD_FRAGMENTS):
            return True
        return re.search(r"[\u0e00-\u0e7f]", text) is not None

    def _is_flat(self, text: str) -> bool:
        flat_markers = ("不错", "很好", "可以", "感觉", "蛮", "挺", "应该")
        return len(text) < 48 or any(marker in text for marker in flat_markers)

    def _has_live_texture(self, text: str) -> bool:
        return any(word in text for word in self.OPENER_WORDS) or "CPU" in text

    def _is_identity_question(self, text: str) -> bool:
        lowered = text.lower()
        return any(
            keyword in lowered
            for keyword in ("你是不是ai", "你是ai", "你是真人", "你是不是人")
        ) or any(keyword in text for keyword in ("你是不是 AI", "你是 AI", "你是真人"))

    def _style_control(self, context: dict[str, Any]) -> dict[str, Any]:
        memory = context.get("memory", {})
        if not isinstance(memory, dict):
            return {}
        style_control = memory.get("style_control", {})
        return style_control if isinstance(style_control, dict) else {}

    def _max_chars(self, style_control: dict[str, Any]) -> int:
        length = style_control.get("length", "normal")
        if length == "short":
            return 78
        if length == "detailed":
            return 130
        return 110

    def _apply_style_control(self, text: str, style_control: dict[str, Any]) -> str:
        result = text
        if self._avoid_phrase(style_control, "CPU"):
            result = result.replace("CPU 风扇", "反应模块")
            result = result.replace("CPU", "反应模块")
        if self._avoid_phrase(style_control, "欸"):
            result = result.replace("可以欸", "可以")
            result = result.replace("欸，", "")
            result = result.replace("欸。", "。")
            result = result.replace("欸", "")
            result = result.replace("可以耶", "可以")
        if self._avoid_phrase(style_control, "好不好"):
            result = re.sub(r"[，,。 ]?好不好[。！？!?]?", "。", result)
        if self._avoid_phrase(style_control, "啦"):
            result = result.replace("啦", "")
        if self._avoid_phrase(style_control, "主人"):
            result = result.replace("主人", "你")

        result = re.sub(r"^[，,。！？!? ]+", "", result)
        result = re.sub(r"\s+", " ", result)
        result = re.sub(r"([。！？!?]){2,}", r"\1", result)
        result = re.sub(r"([，,]){2,}", r"\1", result)
        result = result.replace(" ，", "，").replace(" 。", "。")
        return result.strip() or text

    @staticmethod
    def _avoid_phrase(style_control: dict[str, Any], phrase: str) -> bool:
        avoid = style_control.get("avoid_phrases", {})
        if not isinstance(avoid, dict):
            return False
        try:
            return int(avoid.get(phrase, 0)) > 0
        except (TypeError, ValueError):
            return False

    @staticmethod
    def _choose(seed_text: str, options: tuple[str, ...]) -> str:
        index = sum(ord(ch) for ch in seed_text) % len(options)
        return options[index]

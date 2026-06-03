from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from brain.memory import MemoryManager
from brain.model_memory import ModelMemoryWriter
from brain.ollama_client import OllamaClient, OllamaConfig
from brain.safety import SafetyFilter
from brain.style_polisher import StylePolisher

from .critic import ReplyCritic
from .memory_retriever import MemoryRetriever
from .model_selector import resolve_ollama_models
from .policy import PolicyEngine
from .responder import Responder
from .soul import SoulProfile
from .understanding import UnderstandingEngine


@dataclass
class BrainV2Response:
    user_input: str
    reply: str
    understanding: dict
    retrieved_memory: dict
    policy: dict
    reply_source: str
    critic_summary: str
    memory_summary: str
    model_memory_summary: str


class BrainV2Core:
    def __init__(
        self,
        data_dir: Path,
        llm_mode: str = "ollama",
        ollama_model: str = "auto",
        memory_model: str = "auto",
    ) -> None:
        self.data_dir = Path(data_dir)
        self.llm_mode = llm_mode
        self.model_selection_note = "llm_off"
        if llm_mode != "off":
            selection = resolve_ollama_models(ollama_model, memory_model)
            ollama_model = selection.chat_model
            memory_model = selection.memory_model
            self.model_selection_note = selection.note
        self.chat_model_name = ollama_model
        self.memory_model_name = memory_model
        self.memory = MemoryManager(self.data_dir / "memory.json")
        self.chat_ollama = OllamaClient(
            OllamaConfig(model=ollama_model, timeout_seconds=self._timeout_for_model(ollama_model))
        )
        self.reason_ollama = OllamaClient(
            OllamaConfig(model=memory_model, timeout_seconds=self._timeout_for_model(memory_model))
        )
        self.safety = SafetyFilter()
        self.soul = SoulProfile()
        self.understanding = UnderstandingEngine(
            self.reason_ollama,
            enabled=llm_mode != "off",
        )
        self.retriever = MemoryRetriever()
        self.policy = PolicyEngine()
        self.responder = Responder(self.chat_ollama, self.soul)
        self.critic = ReplyCritic()
        self.polisher = StylePolisher()
        self.model_memory_writer = ModelMemoryWriter(self.reason_ollama)

    def process(self, user_input: str) -> BrainV2Response:
        user_input = user_input.strip()
        safety = self.safety.check_input(user_input)
        if not safety.allowed:
            reply = safety.reply
            self._save_turn(user_input, reply, "safety", "safety", "", "safety")
            return BrainV2Response(
                user_input=user_input,
                reply=reply,
                understanding={"user_act": "safety"},
                retrieved_memory={},
                policy={"mode": "safety"},
                reply_source="safety",
                critic_summary="skipped",
                memory_summary=self.memory.summary(),
                model_memory_summary="skipped=safety",
            )

        memory_snapshot = self.memory.snapshot()
        understanding = self.understanding.analyze(user_input, memory_snapshot).to_dict()
        retrieved = self.retriever.retrieve(memory_snapshot, understanding)
        policy = self.policy.decide(user_input, understanding, retrieved.to_dict()).to_dict()

        if self.llm_mode == "off" and policy.get("mode") != "deterministic":
            policy["mode"] = "deterministic"
            policy["deterministic_reply"] = self._offline_reply(understanding, retrieved.summary())
            policy["reason"] = "offline_fallback"

        reply, source = self.responder.respond(
            user_input=user_input,
            understanding=understanding,
            retrieved_memory=retrieved.to_dict(),
            policy=policy,
        )
        reply, critic_changed, critic_reason = self.critic.review(
            reply=reply,
            user_input=user_input,
            understanding=understanding,
            policy=policy,
        )
        reply = self.polisher.polish(
            reply,
            {
                "user_input": user_input,
                "memory": memory_snapshot,
                "fast_reply": reply,
            },
            source,
        )
        reply = self.safety.filter_output(reply)

        model_memory_summary = self._write_model_memory(
            user_input=user_input,
            ai_reply=reply,
            understanding=understanding,
        )
        topic = understanding.get("topic", "")
        self._save_turn(user_input, reply, understanding.get("user_act", "chat"), "neutral", topic, source)

        return BrainV2Response(
            user_input=user_input,
            reply=reply,
            understanding=understanding,
            retrieved_memory=retrieved.to_dict(),
            policy=policy,
            reply_source=source,
            critic_summary=critic_reason if critic_changed else "ok",
            memory_summary=self.memory.summary(),
            model_memory_summary=model_memory_summary,
        )

    def _write_model_memory(self, user_input: str, ai_reply: str, understanding: dict) -> str:
        if self.llm_mode == "off":
            return "skipped=llm_off"
        fast_decision = self._fast_memory_decision(understanding)
        if fast_decision["items"]:
            summary = self.memory.apply_model_memory(
                fast_decision,
                user_input=user_input,
                ai_reply=ai_reply,
            )
            return f"{summary}, source=fast_memory"
        intent = understanding.get("user_act", "chat")
        if intent in {"memory_query", "identity_query", "self_status_query", "greeting", "topic_switch", "teasing"}:
            return f"skipped=read_only_intent:{intent}"
        if not self.model_memory_writer.should_consider(user_input, intent):
            return "skipped=no_memory_signal"
        decision = self.model_memory_writer.decide(
            user_input=user_input,
            ai_reply=ai_reply,
            memory_snapshot=self.memory.snapshot(),
            intent=intent,
            emotion=understanding.get("emotional_tone", "neutral"),
        )
        summary = self.memory.apply_model_memory(
            decision.to_dict(),
            user_input=user_input,
            ai_reply=ai_reply,
        )
        if decision.error:
            return f"{summary}, error={decision.error}"
        return summary

    @staticmethod
    def _fast_memory_decision(understanding: dict) -> dict:
        items = []
        candidates = understanding.get("stable_memory_candidates", [])
        if isinstance(candidates, list):
            for candidate in candidates[:5]:
                if not isinstance(candidate, dict):
                    continue
                memory_type = str(candidate.get("type", "")).strip()
                value = str(candidate.get("value", "")).strip()
                if memory_type not in {"viewer_name", "viewer_preference", "viewer_dislike"}:
                    continue
                if not value:
                    continue
                items.append(
                    {
                        "type": memory_type,
                        "key": str(candidate.get("key", "")) or memory_type,
                        "value": value[:120],
                        "reason": "explicit_user_memory_candidate",
                        "confidence": 0.9,
                    }
                )

        if understanding.get("user_act") == "feedback":
            target = str(understanding.get("complaint_target", "")).strip()
            if target in {"context", "logic", "memory", "reply_style"}:
                items.append(
                    {
                        "type": "self_improvement",
                        "key": target,
                        "value": f"需要改进{target}能力，优先理解当前输入，不要硬接旧话题",
                        "reason": "explicit_user_feedback",
                        "confidence": 0.85,
                    }
                )

        return {"items": items, "reflection": "fast_memory_candidate"}

    def _save_turn(
        self,
        user_input: str,
        reply: str,
        intent: str,
        emotion: str,
        topic: str,
        source: str,
    ) -> None:
        state_snapshot = {"mood": emotion}
        self.memory.record_interaction(
            user_input=user_input,
            intent=intent,
            emotion=emotion,
            attention_target=topic or "current_input",
            reply_intent="brain_v2",
            state_snapshot=state_snapshot,
        )
        self.memory.update_conversation_context(
            user_input=user_input,
            ai_reply=reply,
            intent=intent,
            emotion=emotion,
            topic=topic,
            reply_source=source,
        )
        self.memory.save()

    @staticmethod
    def _offline_reply(understanding: dict, memory_summary: str) -> str:
        act = understanding.get("user_act", "")
        if act == "memory_query":
            return f"我先看本地记忆：{memory_summary}。如果这里没有，我就不能装作记得。"
        if act == "greeting":
            return "你好，我在线。现在走 Brain v2，大脑会先理解再回复。"
        return "我先用离线脑接住这句。现在没有调用 LLM，所以回答会保守一点。"

    @staticmethod
    def _timeout_for_model(model: str) -> float:
        lowered = model.lower()
        if "qwen2.5:7b" in lowered or "qwen3:8b" in lowered:
            return 90.0
        if "qwen" in lowered:
            return 60.0
        return 24.0

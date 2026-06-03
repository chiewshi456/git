from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .attention import AttentionSystem
from .context import ContextAnalyzer
from .drive import DriveSystem
from .emotion import EmotionEngine
from .feedback import FeedbackInterpreter
from .growth import GrowthSystem
from .intent import IntentClassifier
from .learning import LearningSystem
from .memory import MemoryManager
from .model_memory import ModelMemoryWriter
from .ollama_client import OllamaClient, OllamaConfig
from .persona import Persona, PersonaStore
from .quality import ReplyQualityGate
from .reply_mind import ReplyMind
from .safety import SafetyFilter
from .state import StreamerState
from .style_polisher import StylePolisher
from .teacher import TeachingSystem
from .training_data import TrainingDataCollector


STATE_DELTAS = {
    "greet": {"affection": 1, "loneliness": -2, "curiosity": 1},
    "encourage": {
        "affection": 3,
        "trust": 2,
        "confidence": 2,
        "stress": -3,
        "loneliness": -3,
    },
    "gift": {
        "affection": 5,
        "trust": 1,
        "confidence": 2,
        "stress": -1,
        "playfulness": 1,
    },
    "praise": {"affection": 2, "confidence": 3, "stress": -1, "playfulness": 1},
    "tease": {"playfulness": 4, "stress": 1, "affection": 1, "self_control": -1},
    "insult": {
        "affection": -3,
        "trust": -3,
        "confidence": -5,
        "stress": 8,
        "self_control": -4,
        "playfulness": -2,
    },
    "question": {"curiosity": 3, "focus": 2, "energy": -1},
    "command": {"focus": 3, "stress": 1, "energy": -2, "self_control": -1},
    "emotional_support": {"trust": 2, "curiosity": 2, "stress": 1, "focus": 2},
    "personal_question": {"trust": 1, "curiosity": 4, "focus": 2},
    "silence": {"loneliness": 3, "stress": 1, "energy": -1, "curiosity": 1},
    "feedback": {"curiosity": 2, "focus": 2, "stress": 1},
    "normal": {"energy": -1, "loneliness": -1, "curiosity": 1},
}


@dataclass
class BrainResponse:
    user_input: str
    intent: str
    emotion: str
    drives: list[dict]
    attention_target: str
    reply_intent: str
    final_reply: str
    reply_source: str
    state_summary: str
    memory_summary: str
    context_summary: str = ""
    model_memory_summary: str = ""
    learning_summary: str = ""
    growth_summary: str = ""
    training_summary: str = ""
    teaching_summary: str = ""

    def to_dict(self) -> dict:
        return {
            "user_input": self.user_input,
            "intent": self.intent,
            "emotion": self.emotion,
            "drives": self.drives,
            "attention_target": self.attention_target,
            "reply_intent": self.reply_intent,
            "final_reply": self.final_reply,
            "reply_source": self.reply_source,
            "state_summary": self.state_summary,
            "memory_summary": self.memory_summary,
            "context_summary": self.context_summary,
            "model_memory_summary": self.model_memory_summary,
            "learning_summary": self.learning_summary,
            "growth_summary": self.growth_summary,
            "training_summary": self.training_summary,
            "teaching_summary": self.teaching_summary,
        }


class BrainCore:
    def __init__(
        self,
        data_dir: Path,
        training_dir: Path | None = None,
        llm_mode: str = "auto",
        ollama_model: str = "mika-ai:0.1",
        memory_model: str = "llama3.2:3b",
    ) -> None:
        data_dir = Path(data_dir)
        training_dir = Path(training_dir) if training_dir else data_dir.parent / "training"
        self.persona: Persona = PersonaStore(data_dir / "persona.json").load()
        self.state = StreamerState()
        self.memory = MemoryManager(data_dir / "memory.json")
        self.intent_classifier = IntentClassifier()
        self.emotion_engine = EmotionEngine()
        self.drive_system = DriveSystem()
        self.attention_system = AttentionSystem()
        self.context_analyzer = ContextAnalyzer()
        self.reply_mind = ReplyMind()
        self.quality_gate = ReplyQualityGate()
        self.style_polisher = StylePolisher()
        self.ollama = OllamaClient(OllamaConfig(model=ollama_model))
        self.memory_ollama = OllamaClient(OllamaConfig(model=memory_model))
        self.model_memory_writer = ModelMemoryWriter(self.memory_ollama)
        self.llm_mode = llm_mode
        self.safety_filter = SafetyFilter()
        self.learning_system = LearningSystem()
        self.growth_system = GrowthSystem()
        self.teaching_system = TeachingSystem()
        self.feedback_interpreter = FeedbackInterpreter()
        self.training_collector = TrainingDataCollector(training_dir / "dataset.jsonl")

    def process(self, user_input: str) -> BrainResponse:
        user_input = user_input.strip()

        safety = self.safety_filter.check_input(user_input)
        if not safety.allowed:
            self.state.apply_delta({"stress": 2, "self_control": 1})
            self.state.mood = "focused"
            drives = self.drive_system.compute(self.state)
            state_snapshot = self.state.to_dict()
            self.memory.record_interaction(
                user_input=user_input,
                intent="safety",
                emotion="focused",
                attention_target="conflict",
                reply_intent="set_boundary",
                state_snapshot=state_snapshot,
            )
            self.memory.update_conversation_context(
                user_input=user_input,
                ai_reply=safety.reply,
                intent="safety",
                emotion="focused",
                topic="safety",
                reply_source="safety",
            )
            self.memory.save()
            response = BrainResponse(
                user_input=user_input,
                intent="safety",
                emotion="focused",
                drives=drives,
                attention_target="conflict",
                reply_intent="set_boundary",
                final_reply=safety.reply,
                reply_source="safety",
                state_summary=self.state.debug_summary(),
                memory_summary=self.memory.summary(),
                context_summary="safety",
                model_memory_summary="skipped=safety",
                learning_summary="blocked_by_safety",
                growth_summary=self._growth_summary({}),
                training_summary="recorded=safety_redacted",
            )
            self._record_training_sample(
                response=response,
                learning_result={
                    "topics": [],
                    "feedback": "neutral",
                    "style_signal": "none",
                },
                state_snapshot=state_snapshot,
                sample_type="safety",
            )
            return response

        teaching_result = self.teaching_system.parse(user_input)
        if teaching_result.is_teaching:
            return self._process_teaching(user_input, teaching_result.to_dict())

        feedback_result = self.feedback_interpreter.parse(user_input)
        if feedback_result.is_feedback:
            return self._process_feedback(user_input, feedback_result.to_dict())

        intent_result = self.intent_classifier.classify(user_input)
        intent = intent_result["intent"]
        dialogue_context = self.context_analyzer.analyze(
            user_input=user_input,
            intent=intent,
            memory=self.memory.snapshot(),
        )

        self.state.apply_delta(STATE_DELTAS.get(intent, STATE_DELTAS["normal"]))
        emotion = self.emotion_engine.detect(intent, self.state)
        self.state.mood = emotion

        drives = self.drive_system.compute(self.state)
        attention_target = self.attention_system.select(
            intent=intent,
            emotion=emotion,
            memory=self.memory.snapshot(),
            drives=drives,
        )
        reply_intent = self.reply_mind.choose_intent(
            intent=intent,
            emotion=emotion,
            attention_target=attention_target,
            drives=drives,
            user_input=user_input,
        )

        learning_result = self.learning_system.analyze(
            user_input=user_input,
            intent=intent,
            reply_intent=reply_intent,
        )
        self.memory.apply_learning(learning_result)
        growth_result = self.growth_system.apply(
            memory_data=self.memory.data,
            state=self.state,
            learning_result=learning_result,
            intent=intent,
        )
        drives = self.drive_system.compute(self.state)

        reply_context = {
            "user_input": user_input,
            "persona": self.persona.to_dict(),
            "intent_result": intent_result,
            "emotion": emotion,
            "state": self.state.to_dict(),
            "memory": self.memory.snapshot(),
            "learning": learning_result,
            "growth": growth_result,
            "drives": drives,
            "attention_target": attention_target,
            "dialogue": dialogue_context,
        }
        final_reply, reply_source = self._generate_reply(
            reply_intent=reply_intent,
            intent=intent,
            context=reply_context,
        )
        final_reply = self.safety_filter.filter_output(final_reply)
        model_memory_summary = self._write_model_memory(
            user_input=user_input,
            ai_reply=final_reply,
            intent=intent,
            emotion=emotion,
        )

        state_snapshot = self.state.to_dict()
        self.memory.record_interaction(
            user_input=user_input,
            intent=intent,
            emotion=emotion,
            attention_target=attention_target,
            reply_intent=reply_intent,
            state_snapshot=state_snapshot,
        )
        self.memory.update_conversation_context(
            user_input=user_input,
            ai_reply=final_reply,
            intent=intent,
            emotion=emotion,
            topic=dialogue_context.get("topic", ""),
            reply_source=reply_source,
        )
        self.memory.save()

        response = BrainResponse(
            user_input=user_input,
            intent=intent,
            emotion=emotion,
            drives=drives,
            attention_target=attention_target,
            reply_intent=reply_intent,
            final_reply=final_reply,
            reply_source=reply_source,
            state_summary=self.state.debug_summary(),
            memory_summary=self.memory.summary(),
            context_summary=dialogue_context.get("summary", ""),
            model_memory_summary=model_memory_summary,
            learning_summary=self._learning_summary(learning_result),
            growth_summary=self._growth_summary(growth_result),
            training_summary="recorded=interaction",
        )
        self._record_training_sample(
            response=response,
            learning_result=learning_result,
            state_snapshot=state_snapshot,
            sample_type="interaction",
            growth_result=growth_result,
        )
        return response

    def _process_feedback(self, user_input: str, feedback_result: dict) -> BrainResponse:
        sentiment = feedback_result.get("sentiment", "neutral")
        if sentiment == "positive":
            self.state.apply_delta({"confidence": 2, "trust": 1, "stress": -1, "curiosity": 1})
            emotion = "touched"
        elif sentiment == "negative":
            self.state.apply_delta({"focus": 3, "curiosity": 2, "stress": 1, "confidence": -1})
            emotion = "focused"
        else:
            self.state.apply_delta(STATE_DELTAS["feedback"])
            emotion = "focused"

        self.state.mood = emotion
        self.memory.apply_feedback(feedback_result)

        style_updates = feedback_result.get("style_updates", {})
        learning_result = {
            "topics": ["feedback"],
            "feedback": sentiment,
            "style_signal": style_updates.get("tone", "none")
            if style_updates.get("tone")
            else "none",
            "learned_preferences": [],
            "reply_intent": "learn_from_feedback",
            "intent": "feedback",
            "learning_note": feedback_result.get("note", ""),
        }
        growth_result = self.growth_system.apply(
            memory_data=self.memory.data,
            state=self.state,
            learning_result=learning_result,
            intent="feedback",
        )

        drives = self.drive_system.compute(self.state)
        final_reply = self.feedback_interpreter.reply_for(feedback_result)
        final_reply = self.safety_filter.filter_output(final_reply)
        model_memory_summary = self._write_model_memory(
            user_input=user_input,
            ai_reply=final_reply,
            intent="feedback",
            emotion=emotion,
        )
        state_snapshot = self.state.to_dict()

        self.memory.record_interaction(
            user_input=user_input,
            intent="feedback",
            emotion=emotion,
            attention_target="learning",
            reply_intent="learn_from_feedback",
            state_snapshot=state_snapshot,
        )
        self.memory.update_conversation_context(
            user_input=user_input,
            ai_reply=final_reply,
            intent="feedback",
            emotion=emotion,
            topic="feedback",
            reply_source="feedback",
        )
        self.memory.save()

        response = BrainResponse(
            user_input=user_input,
            intent="feedback",
            emotion=emotion,
            drives=drives,
            attention_target="learning",
            reply_intent="learn_from_feedback",
            final_reply=final_reply,
            reply_source="feedback",
            state_summary=self.state.debug_summary(),
            memory_summary=self.memory.summary(),
            context_summary="feedback",
            model_memory_summary=model_memory_summary,
            learning_summary=self._learning_summary(learning_result),
            growth_summary=self._growth_summary(growth_result),
            training_summary="recorded=feedback",
        )
        self._record_training_sample(
            response=response,
            learning_result=learning_result,
            state_snapshot=state_snapshot,
            sample_type="feedback",
            growth_result=growth_result,
            feedback_result=feedback_result,
        )
        return response

    def _process_teaching(self, user_input: str, teaching_result: dict) -> BrainResponse:
        accepted = teaching_result.get("accepted", False)
        self.memory.apply_teaching(teaching_result)

        learning_result = {
            "topics": ["teaching"],
            "feedback": "positive" if accepted else "negative",
            "style_signal": teaching_result.get("value", "none")
            if teaching_result.get("kind") == "style"
            else "none",
            "learned_preferences": [],
            "reply_intent": "learn_from_teacher",
            "intent": "teaching",
            "learning_note": teaching_result.get("note", ""),
        }
        self.memory.apply_learning(learning_result)
        growth_result = self.growth_system.apply(
            memory_data=self.memory.data,
            state=self.state,
            learning_result=learning_result,
            intent="teaching",
        )

        self.state.apply_delta({"curiosity": 2, "focus": 2, "confidence": 1 if accepted else 0})
        self.state.mood = "curious" if accepted else "focused"
        drives = self.drive_system.compute(self.state)
        final_reply = self.teaching_system.reply_for(
            self.teaching_system.parse(user_input)
        )
        final_reply = self.safety_filter.filter_output(final_reply)
        model_memory_summary = self._write_model_memory(
            user_input=user_input,
            ai_reply=final_reply,
            intent="teaching",
            emotion=self.state.mood,
        )
        state_snapshot = self.state.to_dict()

        self.memory.record_interaction(
            user_input=user_input,
            intent="teaching",
            emotion=self.state.mood,
            attention_target="learning",
            reply_intent="learn_from_teacher",
            state_snapshot=state_snapshot,
        )
        self.memory.update_conversation_context(
            user_input=user_input,
            ai_reply=final_reply,
            intent="teaching",
            emotion=self.state.mood,
            topic="teaching",
            reply_source="teaching",
        )
        self.memory.save()

        response = BrainResponse(
            user_input=user_input,
            intent="teaching",
            emotion=self.state.mood,
            drives=drives,
            attention_target="learning",
            reply_intent="learn_from_teacher",
            final_reply=final_reply,
            reply_source="teaching",
            state_summary=self.state.debug_summary(),
            memory_summary=self.memory.summary(),
            context_summary="teaching",
            model_memory_summary=model_memory_summary,
            learning_summary=self._learning_summary(learning_result),
            growth_summary=self._growth_summary(growth_result),
            training_summary="recorded=teaching",
            teaching_summary=self._teaching_summary(teaching_result),
        )
        self._record_training_sample(
            response=response,
            learning_result=learning_result,
            state_snapshot=state_snapshot,
            sample_type="teaching",
            growth_result=growth_result,
            teaching_result=teaching_result,
        )
        return response

    @staticmethod
    def _learning_summary(learning_result: dict) -> str:
        topics = ",".join(learning_result.get("topics", [])) or "none"
        feedback = learning_result.get("feedback", "neutral")
        style = learning_result.get("style_signal", "none")
        note = learning_result.get("learning_note", "")
        return f"topics={topics}, feedback={feedback}, style={style}, note={note}"

    @staticmethod
    def _growth_summary(growth_result: dict) -> str:
        if not growth_result:
            return "level=1, xp_gain=0, stage=booting"
        return (
            f"level={growth_result.get('level', 1)}, "
            f"xp_gain={growth_result.get('xp_gain', 0)}, "
            f"stage={growth_result.get('stage', 'booting')}, "
            f"level_up={growth_result.get('level_up', False)}"
        )

    @staticmethod
    def _teaching_summary(teaching_result: dict) -> str:
        if not teaching_result:
            return ""
        return (
            f"accepted={teaching_result.get('accepted', False)}, "
            f"kind={teaching_result.get('kind', '')}, "
            f"value={teaching_result.get('value', '')}"
        )

    def _generate_reply(
        self,
        reply_intent: str,
        intent: str,
        context: dict,
    ) -> tuple[str, str]:
        fast_reply = self.reply_mind.generate_reply(
            reply_intent=reply_intent,
            context=context,
        )
        context = dict(context)
        context["fast_reply"] = fast_reply
        repaired, was_repaired, reason = self.quality_gate.repair(fast_reply, context)
        if was_repaired:
            source = f"fast_brain_repaired:{reason}"
            return self.style_polisher.polish(repaired, context, source), source

        if not self._should_use_ollama(intent=intent, reply_intent=reply_intent):
            return self.style_polisher.polish(fast_reply, context, "fast_brain"), "fast_brain"

        llm_reply = self.ollama.generate_reply(context)
        if llm_reply:
            source = f"ollama:{self.ollama.config.model}"
            repaired, was_repaired, reason = self.quality_gate.repair(llm_reply, context)
            if was_repaired:
                source = f"{source}_repaired:{reason}"
            return self.style_polisher.polish(repaired, context, source), source

        if self.llm_mode == "ollama":
            fallback = f"{fast_reply}（本地模型刚刚没接上，我先用快脑顶一下。）"
            return self.style_polisher.polish(
                fallback, context, "fast_brain_ollama_failed"
            ), "fast_brain_ollama_failed"
        repaired, was_repaired, reason = self.quality_gate.repair(fast_reply, context)
        source = f"fast_brain_repaired:{reason}" if was_repaired else "fast_brain"
        return self.style_polisher.polish(repaired, context, source), source

    def _should_use_ollama(self, intent: str, reply_intent: str) -> bool:
        if self.llm_mode == "off":
            return False

        fast_only_intents = {
            "greet",
            "gift",
            "praise",
            "tease",
            "insult",
            "silence",
            "command",
        }
        if intent in fast_only_intents:
            return False

        fast_only_reply_intents = {
            "welcome_viewer",
            "thank_viewer",
            "shy_accept_praise",
            "playful_counter_tease",
            "set_boundary",
            "fill_silence",
            "answer_identity",
            "remember_fact",
            "recall_memory",
        }
        if reply_intent in fast_only_reply_intents:
            return False

        return intent in {
            "normal",
            "question",
            "personal_question",
            "emotional_support",
        }

    def _write_model_memory(
        self,
        user_input: str,
        ai_reply: str,
        intent: str,
        emotion: str,
    ) -> str:
        if self.llm_mode == "off":
            return "skipped=llm_off"
        if intent == "safety":
            return "skipped=safety"
        if not self.model_memory_writer.should_consider(user_input, intent):
            return "skipped=no_memory_signal"

        decision = self.model_memory_writer.decide(
            user_input=user_input,
            ai_reply=ai_reply,
            memory_snapshot=self.memory.snapshot(),
            intent=intent,
            emotion=emotion,
        )
        summary = self.memory.apply_model_memory(
            decision=decision.to_dict(),
            user_input=user_input,
            ai_reply=ai_reply,
        )
        if decision.error:
            return f"{summary}, error={decision.error}"
        if decision.reflection:
            return f"{summary}, reflection={decision.reflection}"
        return summary

    def _record_training_sample(
        self,
        response: BrainResponse,
        learning_result: dict,
        state_snapshot: dict,
        sample_type: str,
        growth_result: dict | None = None,
        teaching_result: dict | None = None,
        feedback_result: dict | None = None,
    ) -> None:
        self.training_collector.record(
            {
                "sample_type": sample_type,
                "user_input": response.user_input,
                "intent": response.intent,
                "emotion": response.emotion,
                "topics": learning_result.get("topics", []),
                "feedback": learning_result.get("feedback", "neutral"),
                "style_signal": learning_result.get("style_signal", "none"),
                "attention_target": response.attention_target,
                "reply_intent": response.reply_intent,
                "ai_reply": response.final_reply,
                "reply_source": response.reply_source,
                "state": state_snapshot,
                "drives": response.drives,
                "memory_context": self.memory.snapshot(),
                "dialogue_context": response.context_summary,
                "model_memory_summary": response.model_memory_summary,
                "growth": growth_result or self.memory.data.get("growth", {}),
                "teaching": teaching_result or {},
                "feedback_detail": feedback_result or {},
            }
        )

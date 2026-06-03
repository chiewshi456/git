from __future__ import annotations

import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path


def tokenize(text: str) -> list[str]:
    text = text.strip().lower()
    ascii_words = re.findall(r"[a-z0-9_]+", text)
    chars = [char for char in text if not char.isspace()]
    bigrams = [text[index : index + 2] for index in range(max(0, len(text) - 1))]
    return ascii_words + chars + bigrams


class NaiveBayesTextClassifier:
    def __init__(self) -> None:
        self.labels: list[str] = []
        self.label_counts: dict[str, int] = {}
        self.token_counts: dict[str, dict[str, int]] = {}
        self.total_tokens: dict[str, int] = {}
        self.vocabulary: list[str] = []
        self.metadata: dict = {}

    def train(self, examples: list[tuple[str, str]], metadata: dict | None = None) -> None:
        label_counts: Counter = Counter()
        token_counts: dict[str, Counter] = defaultdict(Counter)
        vocabulary: set[str] = set()

        for text, label in examples:
            if not label:
                continue
            tokens = tokenize(text)
            label_counts[label] += 1
            token_counts[label].update(tokens)
            vocabulary.update(tokens)

        self.labels = sorted(label_counts)
        self.label_counts = dict(label_counts)
        self.token_counts = {
            label: dict(counter)
            for label, counter in token_counts.items()
        }
        self.total_tokens = {
            label: sum(counter.values())
            for label, counter in token_counts.items()
        }
        self.vocabulary = sorted(vocabulary)
        self.metadata = metadata or {}

    def predict_proba(self, text: str) -> list[dict]:
        if not self.labels:
            return []

        tokens = tokenize(text)
        total_examples = sum(self.label_counts.values())
        vocab_size = max(1, len(self.vocabulary))
        scores = []

        for label in self.labels:
            prior = math.log(self.label_counts[label] / total_examples)
            denominator = self.total_tokens.get(label, 0) + vocab_size
            token_counter = self.token_counts.get(label, {})
            log_score = prior
            for token in tokens:
                log_score += math.log((token_counter.get(token, 0) + 1) / denominator)
            scores.append((label, log_score))

        max_score = max(score for _, score in scores)
        exp_scores = [(label, math.exp(score - max_score)) for label, score in scores]
        total = sum(score for _, score in exp_scores) or 1.0
        return [
            {"label": label, "confidence": round(score / total, 4)}
            for label, score in sorted(exp_scores, key=lambda item: item[1], reverse=True)
        ]

    def predict(self, text: str) -> dict:
        probabilities = self.predict_proba(text)
        if not probabilities:
            return {"label": "", "confidence": 0.0}
        return probabilities[0]

    def to_dict(self) -> dict:
        return {
            "model_type": "multinomial_naive_bayes_char_ngram",
            "labels": self.labels,
            "label_counts": self.label_counts,
            "token_counts": self.token_counts,
            "total_tokens": self.total_tokens,
            "vocabulary": self.vocabulary,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "NaiveBayesTextClassifier":
        model = cls()
        model.labels = list(data.get("labels", []))
        model.label_counts = dict(data.get("label_counts", {}))
        model.token_counts = {
            label: dict(tokens)
            for label, tokens in data.get("token_counts", {}).items()
        }
        model.total_tokens = dict(data.get("total_tokens", {}))
        model.vocabulary = list(data.get("vocabulary", []))
        model.metadata = dict(data.get("metadata", {}))
        return model

    def save(self, path: Path) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as file:
            json.dump(self.to_dict(), file, ensure_ascii=False, indent=2)
            file.write("\n")

    @classmethod
    def load(cls, path: Path) -> "NaiveBayesTextClassifier":
        with Path(path).open("r", encoding="utf-8") as file:
            return cls.from_dict(json.load(file))

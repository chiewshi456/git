from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from text_classifier import NaiveBayesTextClassifier


CLASSIFIERS = ("intent", "feedback", "topic")


def configure_console_encoding() -> None:
    for stream in (sys.stdin, sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")


def load_models(model_dir: Path) -> dict[str, NaiveBayesTextClassifier]:
    models = {}
    for name in CLASSIFIERS:
        path = model_dir / f"{name}_classifier.json"
        if path.exists():
            models[name] = NaiveBayesTextClassifier.load(path)
    return models


def main() -> None:
    configure_console_encoding()

    parser = argparse.ArgumentParser(description="Predict labels with local classifiers.")
    parser.add_argument("text", nargs="*", help="text to classify")
    parser.add_argument(
        "--model-dir",
        default=str(Path(__file__).resolve().parent / "models"),
        help="directory containing classifier JSON files",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=3,
        help="number of predictions to show per classifier",
    )
    args = parser.parse_args()

    text = " ".join(args.text).strip()
    if not text:
        raise SystemExit("Please provide text to classify.")

    models = load_models(Path(args.model_dir))
    if not models:
        raise SystemExit("No models found. Run: python training/train_classifiers.py")

    result = {
        name: model.predict_proba(text)[: args.top_k]
        for name, model in models.items()
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

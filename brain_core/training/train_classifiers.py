from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

from text_classifier import NaiveBayesTextClassifier


CLASSIFIERS = ("intent", "feedback", "topic")


def configure_console_encoding() -> None:
    for stream in (sys.stdin, sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")


def load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []

    rows = []
    with path.open("r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def text_for(row: dict) -> str:
    user_input = row.get("user_input", "")
    teaching = row.get("teaching", {})
    teaching_value = teaching.get("value", "") if isinstance(teaching, dict) else ""
    return f"{user_input}\n{teaching_value}".strip()


def examples_for(rows: list[dict], classifier_name: str) -> list[tuple[str, str]]:
    examples = []
    for row in rows:
        text = text_for(row)
        if not text:
            continue

        if classifier_name == "intent":
            label = row.get("intent", "")
        elif classifier_name == "feedback":
            label = row.get("feedback", "neutral")
        elif classifier_name == "topic":
            topics = row.get("topics", [])
            label = topics[0] if topics else "none"
        else:
            raise ValueError(f"unknown classifier: {classifier_name}")

        if label:
            examples.append((text, label))
    return examples


def train_one(
    rows: list[dict],
    classifier_name: str,
    model_dir: Path,
) -> dict:
    examples = examples_for(rows, classifier_name)
    label_counts = Counter(label for _, label in examples)

    model = NaiveBayesTextClassifier()
    model.train(
        examples,
        metadata={
            "classifier": classifier_name,
            "trained_at": datetime.now().isoformat(timespec="seconds"),
            "training_samples": len(examples),
            "label_counts": dict(label_counts),
            "warning": warning_for(examples, label_counts),
        },
    )
    model_path = model_dir / f"{classifier_name}_classifier.json"
    model.save(model_path)

    return {
        "classifier": classifier_name,
        "samples": len(examples),
        "labels": dict(label_counts),
        "model_path": str(model_path),
        "warning": model.metadata.get("warning", ""),
    }


def warning_for(examples: list[tuple[str, str]], label_counts: Counter) -> str:
    if not examples:
        return "no training samples"
    if len(label_counts) < 2:
        return "only one label present; collect more varied data before trusting predictions"
    rare = [label for label, count in label_counts.items() if count < 3]
    if rare:
        return f"some labels have fewer than 3 samples: {', '.join(rare)}"
    return ""


def main() -> None:
    configure_console_encoding()

    parser = argparse.ArgumentParser(description="Train local text classifiers from JSONL.")
    parser.add_argument(
        "--dataset",
        default=str(Path(__file__).resolve().parent / "dataset.jsonl"),
        help="path to dataset.jsonl",
    )
    parser.add_argument(
        "--model-dir",
        default=str(Path(__file__).resolve().parent / "models"),
        help="directory for classifier JSON files",
    )
    parser.add_argument(
        "--starter",
        default=str(Path(__file__).resolve().parent / "starter_dataset.jsonl"),
        help="optional starter labeled JSONL data",
    )
    parser.add_argument(
        "--no-starter",
        action="store_true",
        help="train only on dataset.jsonl",
    )
    args = parser.parse_args()

    rows = load_jsonl(Path(args.dataset))
    starter_rows = [] if args.no_starter else load_jsonl(Path(args.starter))
    all_rows = rows + starter_rows
    model_dir = Path(args.model_dir)
    model_dir.mkdir(parents=True, exist_ok=True)

    report = {
        "trained_at": datetime.now().isoformat(timespec="seconds"),
        "dataset": str(Path(args.dataset)),
        "starter": "" if args.no_starter else str(Path(args.starter)),
        "dataset_samples": len(rows),
        "starter_samples": len(starter_rows),
        "total_samples": len(all_rows),
        "classifiers": [
            train_one(all_rows, classifier_name, model_dir)
            for classifier_name in CLASSIFIERS
        ],
    }

    report_path = model_dir / "training_report.json"
    with report_path.open("w", encoding="utf-8") as file:
        json.dump(report, file, ensure_ascii=False, indent=2)
        file.write("\n")

    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

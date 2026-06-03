from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path


def load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []

    rows = []
    with path.open("r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def configure_console_encoding() -> None:
    for stream in (sys.stdin, sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")


def print_stats(rows: list[dict]) -> None:
    print(f"samples: {len(rows)}")
    print("intent:", dict(Counter(row.get("intent", "") for row in rows)))
    print("feedback:", dict(Counter(row.get("feedback", "") for row in rows)))
    print("sample_type:", dict(Counter(row.get("sample_type", "") for row in rows)))

    topic_counts = Counter()
    for row in rows:
        topic_counts.update(row.get("topics", []))
    print("topics:", dict(topic_counts))


def main() -> None:
    configure_console_encoding()

    parser = argparse.ArgumentParser(description="Inspect collected brain_core JSONL data.")
    parser.add_argument(
        "--dataset",
        default=str(Path(__file__).resolve().parent / "dataset.jsonl"),
        help="path to dataset.jsonl",
    )
    args = parser.parse_args()

    rows = load_jsonl(Path(args.dataset))
    print_stats(rows)


if __name__ == "__main__":
    main()

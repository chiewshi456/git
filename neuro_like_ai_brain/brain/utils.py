from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def clamp(value: int, minimum: int = 0, maximum: int = 100) -> int:
    return max(minimum, min(maximum, int(value)))


def load_json(path: Path, default: dict[str, Any]) -> dict[str, Any]:
    path = Path(path)
    if not path.exists():
        write_json(path, default)
        return _copy_default(default)

    try:
        with path.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except (json.JSONDecodeError, OSError):
        data = _copy_default(default)

    if not isinstance(data, dict):
        data = _copy_default(default)

    return data


def write_json(path: Path, data: dict[str, Any]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)
        file.write("\n")


def _copy_default(default: dict[str, Any]) -> dict[str, Any]:
    return json.loads(json.dumps(default, ensure_ascii=False))

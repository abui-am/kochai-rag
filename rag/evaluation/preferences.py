"""
Utility helpers to load and format user preference blocks for evaluation scripts.

This module keeps the offline tooling (dataset population + RAGAS evaluation)
in sync with the runtime preference injection path by producing a consistent,
human-readable block that can be embedded in prompts or stored alongside
generated datasets.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional, Sequence
import json
import textwrap


DEFAULT_PREFERENCES_DATA: dict[str, Any] = {
    "profile": {
        "name": "Dummy Evaluator",
        "age": 32,
        "gender": "female",
        "fitness_level": "intermediate",
    },
    "goals": {
        "primary": "fat_loss",
        "secondary": "build_endurance",
    },
    "constraints": {
        "equipment": ["resistance bands", "kettlebell"],
        "time_per_session": "30 minutes",
        "sessions_per_week": 4,
    },
    "preferences": {
        "workout_style": "circuit_training",
        "language": "Bahasa Indonesia (casual)",
        "trainer_tone": "friendly and encouraging",
    },
    "dietary": {
        "style": "plant_forward",
        "restrictions": ["lactose"],
    },
}

DEFAULT_PREFERENCES_BLOCK = textwrap.dedent(
    """\
    - Name: Dummy Evaluator
    - Age: 32
    - Gender: male
    - Fitness Level: intermediate
    - Primary Goal: fat_loss
    - Secondary Goal: build_muscle
    - Equipment: all
    - Time Per Session: 60 minutes
    - Sessions Per Week: 4
    - Workout Style: circuit_training
    - Language: Bahasa Indonesia (casual)
    - Trainer Tone: friendly and encouraging
    - Diet Style: None
    - Dietary Restrictions: lactose, seafood
    """
).strip()


def _format_label(label: str) -> str:
    return label.replace("_", " ").title()


def _format_sequence(value: Sequence[Any]) -> str:
    simple_values = []
    for item in value:
        if isinstance(item, (str, int, float, bool)):
            simple_values.append(str(item))
        else:
            break
    if len(simple_values) == len(value):
        return ", ".join(simple_values)
    return ", ".join(str(item) for item in value)


def format_preferences_block(preferences: dict[str, Any]) -> str:
    """
    Convert a nested preference dictionary into a bullet-point string that
    mirrors the inline format used in the FastAPI runtime.
    """
    lines: list[str] = []

    def _emit(value: Any, label: Optional[str] = None, indent: int = 0) -> None:
        prefix = "  " * indent + "- "
        if isinstance(value, dict):
            heading = f"{prefix}{label}:" if label else f"{prefix}Preferences:"
            lines.append(heading)
            for key, child in value.items():
                _emit(child, _format_label(key), indent + 1)
        elif isinstance(value, (list, tuple)):
            formatted = _format_sequence(value)
            heading = f"{label}: {formatted}" if label else formatted
            lines.append(f"{prefix}{heading}")
        else:
            text = f"{label}: {value}" if label else str(value)
            lines.append(f"{prefix}{text}")

    for key, value in preferences.items():
        _emit(value, _format_label(key))

    return "\n".join(lines)


def _load_preferences_from_file(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"Preferences file not found: {path}")

    raw = path.read_text(encoding="utf-8").strip()
    if not raw:
        raise ValueError(f"Preferences file {path} is empty.")

    if path.suffix.lower() == ".json":
        data = json.loads(raw)
        if not isinstance(data, dict):
            raise ValueError("JSON preferences must be an object.")
        return format_preferences_block(data)

    return raw


def load_preferences(
    preferences_text: Optional[str] = None,
    preferences_file: Optional[str] = None,
    use_default_preferences: bool = False,
) -> Optional[str]:
    """
    Resolve the final preference block for evaluation scripts.

    Preference sources are merged in the order below:
        1. Inline text provided via CLI argument.
        2. External file (JSON for structured data or plain text block).
        3. Built-in dummy profile (when `use_default_preferences` is True).
    """
    chunks: list[str] = []

    if preferences_text:
        chunks.append(preferences_text.strip())

    if preferences_file:
        chunks.append(_load_preferences_from_file(Path(preferences_file)))

    if use_default_preferences:
        chunks.append(DEFAULT_PREFERENCES_BLOCK)

    merged = "\n\n".join(chunk for chunk in chunks if chunk)
    return merged or None



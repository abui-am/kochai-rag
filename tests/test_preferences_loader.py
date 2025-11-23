from pathlib import Path

import json

from rag.evaluation.preferences import (
    DEFAULT_PREFERENCES_BLOCK,
    format_preferences_block,
    load_preferences,
)


def test_format_preferences_block_simple_dict():
    data = {
        "profile": {
            "name": "Test User",
            "fitness_level": "beginner",
        },
        "goals": {
            "primary": "mobility",
        },
    }

    block = format_preferences_block(data)

    assert "- Profile:" in block
    assert "Test User" in block
    assert "Mobility" in block or "mobility" in block


def test_load_preferences_prefers_inline_text(tmp_path: Path):
    json_path = tmp_path / "prefs.json"
    json_path.write_text(json.dumps({"profile": {"name": "File User"}}), encoding="utf-8")

    result = load_preferences(
        preferences_text="- Name: Inline User",
        preferences_file=str(json_path),
        use_default_preferences=False,
    )

    assert "Inline User" in result
    assert "File User" in result


def test_load_preferences_default_block():
    result = load_preferences(use_default_preferences=True)
    assert result == DEFAULT_PREFERENCES_BLOCK


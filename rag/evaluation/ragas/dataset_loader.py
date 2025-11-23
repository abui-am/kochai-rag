from __future__ import annotations

from pathlib import Path
from typing import  List, Dict, Any, Optional
import json


def _normalize_row(obj: Dict[str, Any]) -> Optional[Dict[str, str]]:
    """Normalize a raw dict to the expected schema.

    Expected keys:
      - question: str
      - expected_answer: str (mapped to ground_truth)
    """
    question = obj.get("question")
    expected_answer = obj.get("ground_truth")
    reference_contexts = obj.get("contexts")
    reference_context_ids = obj.get("context_ids")
    if not question or not isinstance(question, str):
        return None
    if not expected_answer or not isinstance(expected_answer, str):
        return None
    return {
        "question": question.strip(),
        "ground_truth": expected_answer.strip(),
        "reference_contexts": reference_contexts,
        "reference_context_ids": reference_context_ids,
    }


def load_dataset(path: str | Path) -> List[Dict[str, str]]:
    """Load evaluation dataset from JSON array or CSV.

    Supported formats:
      - JSON array with objects containing `question`, `expected_answer`.
      - CSV with columns `question`, `expected_answer`.
    Returns a list of dicts with keys: `question`, `ground_truth`.
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Dataset not found: {p}")

    rows: List[Dict[str, str]] = []

   
    data = json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("JSON dataset must be an array of objects")
    for obj in data:
        if isinstance(obj, dict):
            norm = _normalize_row(obj)
            if norm:
                rows.append(norm)
    return rows



from __future__ import annotations

import argparse
import asyncio
import json
import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from openai import OpenAI
from ragas import EvaluationDataset, evaluate
from ragas.metrics import (
    ContextRelevance,
    Faithfulness,
    IDBasedContextRecall,
)

from ragas.metrics import AnswerRelevancy

from ragas.embeddings.base import modern_embedding_factory
from ragas.llms.base import llm_factory
from ragas.prompt import PydanticPrompt

from .dataset_loader import load_dataset
from .adapters import create_knowledge_system, extract_answer_and_contexts
from rag import settings as rag_settings
from rag.evaluation.preferences import load_preferences
llm = llm_factory("ft:gpt-4o-mini-2024-07-18::indo-conversational:CbsQZjOu")
base_llm = llm_factory("gpt-4o-mini")
@dataclass
class EvalConfig:
    dataset_path: Path
    max_samples: Optional[int]
    judge_model: str
    save_dir: Path
    docs_dir: str


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _generate_settings_report(save_dir: Path, eval_results: Optional[Dict[str, Any]] = None, timestamp: Optional[str] = None, list_eval_dataset: Optional[List[Dict[str, Any]]] = None, list_eval_scores: Optional[Dict[str, Any]] = None) -> Path:
    """
    Generate a report of all RAG settings and evaluation scores.
    
    Args:
        save_dir: Directory to save the report
        eval_results: Optional dictionary containing evaluation scores and metrics
        timestamp: Optional timestamp string for filename (format: YYYYMMDDTHHMMSSz)
        list_eval_dataset: Optional list of evaluation dataset
    Returns:
        Path to the saved settings report
    """
    _ensure_dir(save_dir)
        # Generate timestamp for report
    report_timestamp = timestamp or datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    
    settings_dict = rag_settings.get_settings_dict()
    settings_dict["timestamp"] = datetime.utcnow().isoformat() + "Z"
    settings_dict["evaluation_dataset"] = list_eval_dataset
    if list_eval_scores is not None:
        settings_dict["evaluation_scores"] = list_eval_scores
    
    if eval_results is not None:
        settings_dict["results"] = eval_results
    
    report_path = save_dir / f"settings_report_{report_timestamp}.json"
    report_path.write_text(
        json.dumps(settings_dict, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    
    return report_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Run RAGAS evaluation for PaperQA-based RAG")
    parser.add_argument("--dataset", type=str, required=True, help="Path to dataset (json/csv)")
    parser.add_argument("--max-samples", type=int, default=None, help="Max number of samples to evaluate")
    parser.add_argument("--model", type=str, default=os.getenv("RAGAS_JUDGE_MODEL", "gpt-4o-mini"), help="Judge LLM model")
    parser.add_argument("--save-dir", type=str, default="data/evaluation/results", help="Output directory")
    parser.add_argument("--docs-dir", type=str, default="./data/sources/processed", help="Documents directory for RAG")
    parser.add_argument("--preferences-text", type=str, help="Inline user preference block applied across evaluation queries.")
    parser.add_argument("--preferences-file", type=str, help="Path to JSON or plaintext preferences file.")
    parser.add_argument("--use-default-preferences", action="store_true", help="Apply the bundled dummy preference profile.")
    args = parser.parse_args()

    cfg = EvalConfig(
        dataset_path=Path(args.dataset),
        max_samples=args.max_samples,
        judge_model=args.model,
        save_dir=Path(args.save_dir),
        docs_dir=args.docs_dir,
    )

    eval_timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")


    rows = load_dataset(cfg.dataset_path)
    if cfg.max_samples is not None:
        rows = rows[: cfg.max_samples]

    system = create_knowledge_system(docs_dir=cfg.docs_dir, openai_api_key=os.getenv("OPENAI_API_KEY"))
    dataset = []

    preferences_block = load_preferences(
        preferences_text=args.preferences_text,
        preferences_file=args.preferences_file,
        use_default_preferences=args.use_default_preferences,
    )

    evaluation_output = Path("evaluation_dataset.json")
    if preferences_block:
        evaluation_output = evaluation_output.with_name(
            f"{evaluation_output.stem}-preferenced{evaluation_output.suffix}"
        )

    if preferences_block:
        print("Applying shared user preferences for evaluation:\n", preferences_block)
    else:
        print("Evaluation running without user preferences (baseline).")


    async def _ask(q: str):
        return await system.query(q, preferences=preferences_block)

    for item in rows:

        q = item["question"]
        gt = item.get("ground_truth")
        rc = item.get("reference_contexts")
        rcids = item.get("reference_context_ids")
        try:
            answer_response = asyncio.run(_ask(q))
            if len(answer_response.session.used_contexts) == 0:
                answer_response = asyncio.run(_ask(q))
                if len(answer_response.session.used_contexts) == 0:
                    answer_response = asyncio.run(_ask(q))
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            answer_response = loop.run_until_complete(_ask(q))
            loop.close()


        answer_text, ctxs, context_ids = extract_answer_and_contexts(answer_response)
        dataset.append({
            "user_input": q,
            "response": answer_text,
            "retrieved_contexts": ctxs,
            "reference_contexts" :rc,
            "reference_context_ids" : rcids,
            "retrieved_context_ids" : context_ids,
            "reference": gt,
            "preferences": preferences_block,
        })

    with evaluation_output.open('w', encoding='utf-8') as f:
        json.dump(dataset, f, ensure_ascii=False, indent=2)

    print(f"Saved evaluation dataset to {evaluation_output}")
    evaluation_dataset = EvaluationDataset.from_list(dataset)
    result = evaluate(dataset=evaluation_dataset,metrics=[IDBasedContextRecall(), Faithfulness(), AnswerRelevancy(llm=llm), ContextRelevance()],llm=base_llm)
    print(result)

    list_eval_dataset = evaluation_dataset.to_list()
    _generate_settings_report(
        list_eval_scores=result.scores,
        save_dir=cfg.save_dir, list_eval_dataset= list_eval_dataset, eval_results=result._repr_dict, timestamp=eval_timestamp)



if __name__ == "__main__":
    main()



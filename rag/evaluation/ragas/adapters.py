from __future__ import annotations

from typing import List, Tuple

from paperqa.agents.models import AnswerResponse

from rag.agentic_workflow import FitnessKnowledgeSystem


def extract_answer_and_contexts(answer_response: AnswerResponse) -> Tuple[str, List[str]]:
    """Extract answer text and a list of contexts from PaperQA AnswerResponse.

    This function is defensive to handle different response shapes.
    """
    answer_text: str = ""
    contexts: List[str] = []
    context_ids: List[str] = []

    answer_text = answer_response.session.raw_answer
    used_contexts = answer_response.session.used_contexts
    for context in answer_response.session.contexts:
        if context.id in used_contexts:
            contexts.append(context.context)
            context_ids.append(context.text.doc.dockey)

    return answer_text, contexts, context_ids


def create_knowledge_system(docs_dir: str = "./data/sources/processed", openai_api_key: str | None = None) -> FitnessKnowledgeSystem:
    """Create the PaperQA-based system."""
    return FitnessKnowledgeSystem(docs_dir=docs_dir, openai_api_key=openai_api_key, auto_index=True)



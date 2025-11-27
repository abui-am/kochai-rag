"""
Utility functions for RAG system operations.
"""
import os
from typing import Dict, Any, Optional

from openai import AsyncOpenAI
from rag import settings as rag_settings

# Initialize vanilla client
vanilla_client: Optional[AsyncOpenAI] = None

VANILLA_MODEL_NAME = rag_settings.PRIMARY_LLM
VANILLA_TEMPERATURE = 0
VANILLA_SYSTEM_PROMPT = (
    "You are a supportive, certified Indonesian fitness coach. "
    "Answer in Bahasa Indonesia with concise, actionable guidance.\n"
    f"{rag_settings.get_fitness_coach_prompt()}"
)


def _extract_response_text(response: Any) -> str:
    """Extract assistant text from OpenAI Responses API objects."""
    text = getattr(response, "output_text", None)
    if text:
        return text.strip()

    output = getattr(response, "output", None)
    if not output:
        return ""

    collected: list[str] = []
    for block in output:
        for content in getattr(block, "content", []):
            content_text = getattr(content, "text", None)
            if content_text:
                collected.append(content_text)
            value = getattr(getattr(content, "text", None), "value", None)
            if value:
                collected.append(value)
    return "\n".join(collected).strip()


def initialize_vanilla_client(api_key: Optional[str] = None) -> None:
    """Initialize the vanilla OpenAI client."""
    global vanilla_client
    if api_key:
        vanilla_client = AsyncOpenAI(api_key=api_key)
    elif os.getenv("OPENAI_API_KEY"):
        vanilla_client = AsyncOpenAI()
    else:
        vanilla_client = None


async def vanilla_query(
    question_text: str,
    preferences: Optional[str] = None
) -> Dict[str, Any]:
    """Process a GPT-only query for comparison against RAG responses.

    Args:
        question_text: The fitness question to ask
        preferences: Optional user preferences to apply

    Returns:
        Dictionary containing the response with answer, model, usage, etc.
    """
    if vanilla_client is None:
        raise RuntimeError("Vanilla GPT client not ready. Check OPENAI_API_KEY configuration.")

    try:
        vanilla_prompt = VANILLA_SYSTEM_PROMPT
        user_prompt = question_text.strip()
        if preferences:
            vanilla_prompt += f"\n\nPreferensi pengguna:\n{preferences}"

        response = await vanilla_client.responses.create(
            model=VANILLA_MODEL_NAME,
            temperature=VANILLA_TEMPERATURE,
            input=[
                {
                    "role": "system",
                    "content": [{"type": "input_text", "text": vanilla_prompt}],
                },
                {
                    "role": "user",
                    "content": [{"type": "input_text", "text": user_prompt}],
                },
                {
                    "role" : "system",
                    "content": [{"type": "input_text", "text": "Integrate Reasoning Summary, Action Plan, and Reflection Question into the answer seamlessly. Reject any question without fitness related context. Also please make the answer like conversation"}],
                },

            ],
        )

        answer_text = _extract_response_text(response)
        if not answer_text:
            raise RuntimeError("GPT returned an empty response")

        usage_payload: Dict[str, Any] = {}
        usage_obj = getattr(response, "usage", None)
        if usage_obj is not None:
            if hasattr(usage_obj, "model_dump"):
                usage_payload = usage_obj.model_dump()
            elif hasattr(usage_obj, "dict"):
                usage_payload = usage_obj.dict()
            else:
                usage_payload = usage_obj  # type: ignore[assignment]

        return {
            "answer": answer_text,
            "model": getattr(response, "model", VANILLA_MODEL_NAME),
            "usage": usage_payload,
            "query": question_text,
            "status": "success",
            "preferences": preferences,
        }
    except Exception as e:
        raise RuntimeError(f"Error processing vanilla query: {str(e)}")

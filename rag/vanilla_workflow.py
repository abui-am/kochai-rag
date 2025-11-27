"""
Vanilla Fitness Query System using direct LLM calls without RAG.
This provides a clean interface for vanilla queries similar to the RAG workflow.
"""
import logging
from typing import Dict, Any, Optional

from rag.utils import vanilla_query, initialize_vanilla_client

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VanillaFitnessSystem:
    """Simple vanilla fitness query system using direct LLM calls."""

    def __init__(self, openai_api_key: str = None):
        """
        Initialize the vanilla fitness query system.

        Args:
            openai_api_key: OpenAI API key for LLM operations
        """
        self.openai_api_key = openai_api_key
        self.client_ready = False

        # Initialize the vanilla client
        initialize_vanilla_client(openai_api_key)
        self.client_ready = True
        logger.info("Vanilla fitness system initialized")

    def is_ready(self) -> bool:
        """Check if the vanilla client is ready for queries."""
        return self.client_ready

    async def query(self, question: str, preferences: Optional[str] = None) -> Dict[str, Any]:
        """
        Query using direct LLM call without RAG retrieval.

        Args:
            question: The user's fitness-related question
            preferences: Optional user preferences to apply

        Returns:
            Dictionary containing the answer and metadata
        """
        try:
            if not self.is_ready():
                logger.error("Vanilla client not ready")
                return {
                    "answer": "",
                    "model": "",
                    "usage": {},
                    "query": question,
                    "status": "error",
                    "preferences": preferences,
                    "error": "Vanilla client not ready. Check OPENAI_API_KEY configuration."
                }

            result = await vanilla_query(question, preferences)
            return result

        except Exception as e:
            logger.error(f"Error processing vanilla query: {e}")
            return {
                "answer": "",
                "model": "",
                "usage": {},
                "query": question,
                "status": "error",
                "preferences": preferences,
                "error": str(e)
            }


async def create_vanilla_fitness_system(openai_api_key: str = None) -> VanillaFitnessSystem:
    """
    Create and initialize a vanilla fitness query system.

    Args:
        openai_api_key: OpenAI API key for LLM operations

    Returns:
        Initialized VanillaFitnessSystem instance
    """
    try:
        system = VanillaFitnessSystem(openai_api_key=openai_api_key)
        logger.info("Vanilla fitness system created successfully")
        return system

    except Exception as e:
        logger.error(f"Failed to create vanilla fitness system: {e}")
        raise RuntimeError(f"Failed to initialize vanilla fitness system: {e}")


# Aliases for backward compatibility
VanillaWorkflow = VanillaFitnessSystem
create_vanilla_workflow = create_vanilla_fitness_system

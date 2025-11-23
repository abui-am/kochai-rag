"""
Simplified Fitness Knowledge Retrieval using PaperQA.
This provides a clean interface to query fitness research documents.
Optimized for speed with parallel processing and efficient settings.
"""
import logging
from pathlib import Path
from typing import Dict, Any, Optional

from paperqa import  ask, Settings
from paperqa.agents.search import get_directory_index
from paperqa.agents.models import AnswerResponse
from openai import OpenAI
from paperqa.prompts import CANNOT_ANSWER_PHRASE, CITATION_KEY_CONSTRAINTS, select_paper_prompt

from rag.docs_cache import (
    save_docs_cache, load_docs_cache, clear_docs_cache, get_cache_info
)
from rag import settings as rag_settings

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FitnessKnowledgeSystem:
    """Simple fitness knowledge system using PaperQA with startup indexing and pickle caching."""
    
    def __init__(self, docs_dir: str = "./data/sources/processed", 
                 openai_api_key: str = None, auto_index: bool = True,
                 cache_dir: str = "./.cache"):
        """
        Initialize the fitness knowledge system.
    
        Args:
            docs_dir: Directory containing the source documents
            openai_api_key: OpenAI API key for LLM operations
            auto_index: Whether to build the index automatically on startup
            cache_dir: Directory to store pickle cache of indexed documents
        """
        self.docs_dir = docs_dir
        self.openai_api_key = openai_api_key
        self.openai = OpenAI(api_key=openai_api_key)
        self.auto_index = auto_index
        self.cache_dir = cache_dir
        self.cache_path = str(Path(cache_dir) / "docs_index.pkl")
        self.index_built = False
        self.settings: Optional[Settings] = None
        self.cached_docs = None
        
        Path(cache_dir).mkdir(parents=True, exist_ok=True)
        
        docs_path = Path(docs_dir)
        if not docs_path.exists():
            docs_path.mkdir(parents=True, exist_ok=True)
        
        doc_files = list(docs_path.glob("*.pdf")) + list(docs_path.glob("*.txt"))
        logger.info(f"Found {len(doc_files)} documents in {docs_dir}")
        logger.info(f"Index cache directory: {cache_dir}")
    
    def has_documents(self) -> bool:
        """Check if there are any documents available for RAG."""
        return self.get_document_count() > 0
    
    def _create_settings(self, agent_prefs: Optional[str] = None) -> Settings:
        """Create PaperQA settings with optimized configuration.

        agent_prefs: Optional string of user preferences to inject into agent_prompt only.
        Settings are sourced from rag.settings module for consistency across codebase.
        """
        settings = Settings(
            paper_directory=self.docs_dir,
        )

        # Evidence settings from rag.settings
        settings.answer.evidence_k = rag_settings.EVIDENCE_K
        settings.answer.evidence_summary_length = rag_settings.EVIDENCE_SUMMARY_LENGTH
        settings.answer.evidence_skip_summary = rag_settings.EVIDENCE_SKIP_SUMMARY

        # Answer generation settings from rag.settings
        settings.answer.answer_max_sources = rag_settings.ANSWER_MAX_SOURCES
        settings.answer.answer_length = rag_settings.ANSWER_LENGTH
        settings.answer.max_concurrent_requests = rag_settings.MAX_CONCURRENT_REQUESTS
        settings.answer.answer_filter_extra_background = rag_settings.ANSWER_FILTER_EXTRA_BACKGROUND

        # Embedding and retrieval settings from rag.settings
        settings.embedding = rag_settings.EMBEDDING_MODEL
        settings.texts_index_mmr_lambda = rag_settings.TEXTS_INDEX_MMR_LAMBDA

        # Paper selection prompt from rag.settings
        settings.prompts.select = rag_settings.build_select_paper_prompt(agent_prefs)
        settings.prompts.summary = rag_settings.SUMMARIZATION_PROMPT
        # LLM models from rag.settings
        settings.llm = rag_settings.PRIMARY_LLM
        settings.agent.agent_llm = rag_settings.AGENT_LLM
        settings.summary_llm = rag_settings.SUMMARY_LLM
        settings.batch_size = rag_settings.BATCH_SIZE
        
        # Agent settings from rag.settings
        settings.agent.timeout = rag_settings.AGENT_TIMEOUT
        settings.agent.agent_evidence_n = rag_settings.AGENT_EVIDENCE_N
        settings.agent.search_count = rag_settings.AGENT_SEARCH_COUNT

        # Agent prompt with user preferences
        settings.agent.agent_prompt = rag_settings.get_agent_prompt_with_preferences(agent_prefs)

        # QA prompt from rag.settings
        settings.prompts.qa = rag_settings.get_qa_prompt_v2(user_preferences=agent_prefs)

        logger.info("Settings created with agent_prefs: %s", agent_prefs)
        return settings
    
    async def build_index(self) -> bool:
        """
        Build the PaperQA index on startup with pickle caching.
        
        This method attempts to load a cached index first. If cache is valid,
        it uses the cached Docs object. Otherwise, it rebuilds the index and
        saves it to cache for faster future startup.
        """
        try:
            if self.index_built:
                return True
                
            if not self.has_documents():
                return False
            
            logger.info("Building index...")
            
            # Create settings
            self.settings = self._create_settings()
            
            cached_docs, is_valid = load_docs_cache(self.cache_path, self.docs_dir)
            
            # Step 1: Cache is valid and exists - load from cache
            if is_valid and cached_docs is not None:
                self.cached_docs = cached_docs
                self.index_built = True
                logger.info("Index loaded from cache (faster startup)")
                return True
            
            # Step 2: Cache is invalid or doesn't exist - rebuild index
            if cached_docs is not None:
                logger.info("Cache exists but is stale (documents changed). Rebuilding index...")
            else:
                logger.info("Cache not found. Building new index...")
            
            built_index = await get_directory_index(settings=self.settings)
        
            self.cached_docs = built_index
            
            try:
                indexed_files = await built_index.index_files
                logger.info(f"Indexed {len(indexed_files)} files")
            except Exception as e:
                logger.info(f"Index built (file count not available: {e})")
            
            # Step 3: Save to cache for future use
            logger.info("Saving Docs to pickle cache...")
            save_success = save_docs_cache(built_index, self.cache_path, self.docs_dir)
            if save_success:
                logger.info(f"Cache saved to {self.cache_path}")
            else:
                logger.warning("Failed to save cache (non-fatal, continuing)")
            
            self.index_built = True
            return True
            
        except Exception as e:
            logger.error(f"Failed to build index: {e}")
            self.index_built = False
            return False
    
    async def ensure_index_ready(self) -> bool:
        """Ensure the index is built and ready for queries."""
        if not self.index_built and self.auto_index:
            return await self.build_index()
        return self.index_built or not self.auto_index
    
    async def query(self, question: str, preferences: Optional[str] = None) -> AnswerResponse:
        """
        Query the fitness knowledge base using optimized 2-API approach:
        1. Get vanilla LLM response first
        2. Pass vanilla response to PaperQA for enhanced RAG response (eliminates 3rd API call)
        
        Args:
            question: The user's fitness-related question
            
        Returns:
            Dictionary containing the answer and metadata
        """
        try:
            if self.has_documents():
                if not await self.ensure_index_ready():
                    logger.warning("Index not ready, falling back to vanilla response")
                    return AnswerResponse(
                        answer='',
                        context='',
                        sources=[],
                        response=None
                    )
                
                settings = self._create_settings(agent_prefs=preferences)
            
            rag_answer:AnswerResponse = await ask(question, settings=settings)
         
            return rag_answer
            
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            return AnswerResponse(
                answer='',
                context='',
                sources=[],
                response=None
            )
    
    def get_document_count(self) -> int:
        """Get the number of documents in the system."""
        docs_path = Path(self.docs_dir)
        if not docs_path.exists():
            return 0
        
        doc_files = list(docs_path.rglob("*.pdf")) + list(docs_path.rglob("*.txt"))
        return len(doc_files)

    def clear_cache(self) -> bool:
        """
        Clear the pickle cache.
        
        Returns:
            True if cache was cleared, False otherwise
        """
        return clear_docs_cache(self.cache_path)
    
    def get_cache_info(self) -> Optional[dict]:
        """
        Get information about the current cache without loading the full Docs.
        
        Returns:
            Dictionary with cache metadata or None if cache doesn't exist
        """
        return get_cache_info(self.cache_path)
    
    def get_cache_status(self) -> Dict[str, Any]:
        """
        Get detailed status of the cache and system state.
        
        Returns:
            Dictionary with comprehensive cache and system status
        """
        cache_info = self.get_cache_info()
        
        return {
            "index_built": self.index_built,
            "cache_exists": cache_info is not None,
            "cache_info": cache_info,
            "cache_path": self.cache_path,
            "docs_dir": self.docs_dir,
            "document_count": self.get_document_count(),
            "has_cached_docs": self.cached_docs is not None
        }

async def create_fitness_knowledge_system(docs_dir: str = "./data/sources/processed", 
                                        openai_api_key: str = None, 
                                        auto_index: bool = True,
                                        cache_dir: str = "./.cache") -> FitnessKnowledgeSystem:
    """
    Create and initialize a fitness knowledge system using PaperQA with startup indexing and pickle caching.
    
    Args:
        docs_dir: Directory containing the source documents
        openai_api_key: OpenAI API key for LLM operations
        auto_index: Whether to build the index automatically on startup
        cache_dir: Directory to store pickle cache of indexed documents
        
    Returns:
        Initialized FitnessKnowledgeSystem instance with index built if auto_index=True
    """
    try:
        system = FitnessKnowledgeSystem(
            docs_dir=docs_dir, 
            openai_api_key=openai_api_key, 
            auto_index=auto_index,
            cache_dir=cache_dir
        )
        
        # Build index on startup if auto_index is enabled
        if auto_index and system.has_documents():
            logger.info("Building index on startup...")
            index_success = await system.build_index()
            if index_success:
                logger.info("Fitness knowledge system created with PaperQA index")
            else:
                logger.warning("Fitness knowledge system created but index building failed")
        else:
                logger.info("Fitness knowledge system created without index building")
        return system
        
    except Exception as e:
        logger.error(f"Failed to create fitness knowledge system: {e}")
        raise RuntimeError(f"Failed to initialize fitness knowledge system: {e}")

AgenticWorkflow = FitnessKnowledgeSystem
create_agentic_workflow = create_fitness_knowledge_system

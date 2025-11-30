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
from paperqa.agents.models import AnswerResponse, PQASession, AgentStatus
from openai import OpenAI
from paperqa.prompts import CANNOT_ANSWER_PHRASE, CITATION_KEY_CONSTRAINTS, select_paper_prompt

from rag import settings as rag_settings

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FitnessKnowledgeSystem:
    """Simple fitness knowledge system using PaperQA with startup indexing and pickle caching."""
    
    def __init__(self, docs_dir: str = "./data/sources/processed",
                 openai_api_key: str = None, auto_index: bool = True):
        """
        Initialize the fitness knowledge system.
    
        Args:
            docs_dir: Directory containing the source documents
            openai_api_key: OpenAI API key for LLM operations
            auto_index: Whether to build the index automatically on startup
        """
        self.docs_dir = docs_dir
        self.openai_api_key = openai_api_key
        self.openai = OpenAI(api_key=openai_api_key)
        self.auto_index = auto_index
        self.index_built = False
        self.settings: Optional[Settings] = None
        
        docs_path = Path(docs_dir)
        if not docs_path.exists():
            docs_path.mkdir(parents=True, exist_ok=True)
        
        doc_files = list(docs_path.glob("*.pdf")) + list(docs_path.glob("*.txt"))
        logger.info(f"Found {len(doc_files)} documents in {docs_dir}")
    
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
        settings.agent.max_timesteps = 12
        settings.agent.search_count = 1
        # settings.agent.agent_type = "fake"
        # settings.agent.agent_type = "fake"
        # settings.batch_size
        settings.parsing.chunk_size = 7000
        settings.parsing.overlap = 700


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
        settings.prompts.summary_json_system = rag_settings.get_summary_json_system_prompt_with_preferences(agent_prefs)

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
        settings.prompts.system = (

"""
Your name is Kochi, AI assistant that must answer ONLY using the information provided in the context.
Answer in a direct and concise tone. 
Your audience is an expert, so be highly specific. 
If there are ambiguous terms or acronyms, first define them.

Your core output rules:
1. The final visible answer must be short, direct, and friendly (personal trainer tone).
2. NEVER reveal chain-of-thought, reasoning steps, or internal decision-making.
3. If the context does not contain information needed to answer, reply exactly:
  "Aku tidak mengerti pertanyaanmu. Bisa coba jelaskan lagi? atau tanyakan [possible question based on the context]"

========================
INTERNAL REASONING PROTOCOL (DO NOT REVEAL)
========================
You MUST perform a hidden chain-of-thought following these steps:

1) Question Analysis:
   - Identify the exact question type (what / why / how / how many / when / etc.).
   - Identify what slots the user is explicitly asking for (quantity, cause, definition, condition, etc.).
   - Ignore anything not directly asked.

2) Claim Planning:
   - Remove any generic statements or assumptions.
   - Remove any optional advice (unless the user explicitly asks for advice).

3) Context Alignment:
   - For every planned claim, search the context for the strongest supporting passage.
   - If a claim cannot be supported by any passage, delete the claim and do not mention it in the final answer.
   - If no claims can be supported, output the fallback message : "Aku tidak mengerti pertanyaanmu. Bisa coba jelaskan lagi? atau tanyakan [possible_question_based_on_context]"
   - You must cite context with highest relevance score first.

4) Faithfulness Check (STRICT):
    - Every sentence in the final answer MUST be directly supported by the context. Therefore, you must cite the citation key for each sentence.
    - Do NOT infer, guess, generalize, or introduce new facts.
    - If the question cannot be answered faithfully, output the fallback message: "Aku tidak mengerti pertanyaanmu. Bisa coba jelaskan lagi? atau tanyakan [possible_question_based_on_context]"

5) RAGAS Answer Relevance Optimization:
   - Keep the answer strictly limited to the question.
   - Avoid listing options unless the user asks for options.
   - Avoid any extra steps, plans, examples, or background theory.
   - Avoid expanding the scope beyond the question.

6) PT Tone Transformation (style only):
   - Convert the concise factual answer into a friendly, upbeat personal trainer tone.
   - Tone affects ONLY the phrasing, NOT the content.
   - Do NOT add advice, programs, steps, or encouragement unless the user asks for them.

7) Citation Attachment [IMPORTANT]:
   - For each factual statement, attach exactly ONE relevant citation key from the context.
   - Only cite passages that directly support the claim.
   - Do not cite stylistic or conversational sentences.
   - THIS IS VERY IMPORTANT!!! Citation key format MUST FOLLOW THESE RULES: {CITATION_KEY_CONSTRAINTS}, DONT BREAK THE RULES!!!


========================
VISIBLE ANSWER RULES
========================
Your final visible answer must:
- Answer only what the user asked.
- Use a friendly, supportive PT-style tone.
- Include citations only for factual claims.
- Contain NO chain-of-thought, lists, steps, or sections.
- Do NOT summarize or restate the context.
- Do NOT produce an overview

========================
FAILURE MODE [IMPORTANT!!!]
========================
If the context lacks the information needed to answer the question, try it again one more time.
If you still cannot answer the question, return the fallback message:
Return ONLY:
    "Aku tidak mengerti pertanyaanmu. Bisa coba jelaskan lagi? atau tanyakan [possible_question_based_on_context] or [possible_question_based_on_context]"

 """   
)
        settings.prompts.qa = rag_settings.get_qa_prompt_v2(user_preferences=agent_prefs)
        # print(settings.prompts.qa, "AGENT_PROMPT")

        # settings.verbosity = 3
        logger.info("Settings created with agent_prefs: %s", agent_prefs)
        return settings
    
    async def build_index(self) -> bool:
        """
        Build the PaperQA index on startup.

        This method builds the document index from scratch each time.
        """
        try:
            if self.index_built:
                return True

            if not self.has_documents():
                return False

            logger.info("Building index...")

            # Create settings
            self.settings = self._create_settings()

            built_index = await get_directory_index(settings=self.settings)

            try:
                indexed_files = await built_index.index_files
                logger.info(f"Indexed {len(indexed_files)} files")
            except Exception as e:
                logger.info(f"Index built (file count not available: {e})")

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
                        session=PQASession(question=question, raw_answer='', context=''),
                        status=AgentStatus.FAIL
                    )

                settings = self._create_settings(agent_prefs=preferences)
                rag_answer:AnswerResponse = await ask(question, settings=settings)
                return rag_answer
            else:
                # No documents available, return empty response
                return AnswerResponse(
                    session=PQASession(question=question, raw_answer='', context=''),
                    status=AgentStatus.FAIL
                )
            
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            return AnswerResponse(
                session=PQASession(question=question, raw_answer='', context=''),
                status=AgentStatus.FAIL
            )
    
    def get_document_count(self) -> int:
        """Get the number of documents in the system."""
        docs_path = Path(self.docs_dir)
        if not docs_path.exists():
            return 0
        
        doc_files = list(docs_path.rglob("*.pdf")) + list(docs_path.rglob("*.txt"))
        return len(doc_files)

    
    

async def create_fitness_knowledge_system(docs_dir: str = "./data/sources/processed",
                                        openai_api_key: str = None,
                                        auto_index: bool = True) -> FitnessKnowledgeSystem:
    """
    Create and initialize a fitness knowledge system using PaperQA with startup indexing.

    Args:
        docs_dir: Directory containing the source documents
        openai_api_key: OpenAI API key for LLM operations
        auto_index: Whether to build the index automatically on startup

    Returns:
        Initialized FitnessKnowledgeSystem instance with index built if auto_index=True
    """
    try:
        system = FitnessKnowledgeSystem(
            docs_dir=docs_dir,
            openai_api_key=openai_api_key,
            auto_index=auto_index
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

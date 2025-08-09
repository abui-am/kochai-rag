"""
Core RAG implementation using paper-qa.
"""
from pathlib import Path
from typing import List, Dict, Any
from paperqa import Docs
import asyncio
from functools import partial

class FitnessRAG:
    """RAG implementation for fitness knowledge retrieval."""
    
    def __init__(self, docs_dir: str = "./data/sources/processed_data"):
        """
        Initialize the RAG system.
        
        Args:
            docs_dir: Directory containing the source documents
        """
        # Use a widely compatible model with our pinned deps
        self.docs = Docs(llm="gpt-4o-mini")
        self.docs_dir = Path(docs_dir)
        self._load_documents()
    
    def _load_documents(self) -> None:
        """Load documents from the specified directory."""
        try:
            # Support both PDFs and text summaries
            for pattern in ("*.pdf", "*.txt"):
                for doc_file in self.docs_dir.glob(pattern):
                    citation = f"Research Source ({doc_file.stem})"
                    self.docs.add(
                        path=str(doc_file),
                        citation=citation,
                        key=doc_file.stem,
                        chunk_chars=1200
                    )
        except Exception as e:
            raise Exception(f"Error loading documents: {e}")
    
    async def query(self, question: str) -> Dict[str, Any]:
        """
        Query the knowledge base.
        
        Args:
            question: The user's fitness-related question
            
        Returns:
            Dict containing the answer and sources
        """
        try:
            loop = asyncio.get_event_loop()

            # First attempt with balanced params
            answer = await loop.run_in_executor(
                None,
                partial(
                    self.docs.query,
                    question,
                    k=20,
                    max_sources=8,
                    length_prompt="about 120 words",
                    marginal_relevance=True,
                ),
            )

            answer_text = str(answer)
            sources = [str(ref) for ref in answer.references]
            if ("insufficient information" in answer_text.lower()) or (len(sources) == 0):
                # Retry with wider search if the first attempt couldn't answer
                answer = await loop.run_in_executor(
                    None,
                    partial(
                        self.docs.query,
                        question,
                        k=40,
                        max_sources=12,
                        length_prompt="about 150 words",
                        marginal_relevance=True,
                    ),
                )
                answer_text = str(answer)
                sources = [str(ref) for ref in answer.references]

            return {
                "answer": answer_text,
                "sources": sources,
                "context": answer.context,
            }

        except Exception as e:
            raise Exception(f"Error processing query: {e}")
    
    def get_loaded_documents(self) -> List[str]:
        """Get list of loaded document names."""
        docs: List[str] = []
        for pattern in ("*.pdf", "*.txt"):
            docs.extend([str(p.name) for p in self.docs_dir.glob(pattern)])
        return sorted(docs)
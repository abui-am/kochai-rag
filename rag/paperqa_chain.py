"""
PaperQA-based RAG implementation for fitness knowledge retrieval.
"""
from typing import Dict, Any
from paperqa import Docs
from langchain_community.tools import Tool

class FitnessRAG:
    def __init__(self, docs_dir: str = "./data/sources"):
        """Initialize the RAG system with documents from the specified directory."""
        self.docs = Docs()
        self.docs_dir = docs_dir

    def query_documents(self, question: str) -> Dict[str, Any]:
        """
        Query the documents for relevant information using PaperQA.
        
        Args:
            question: The user's fitness-related question
            
        Returns:
            Dict containing the answer, context, and sources
        """
        try:
            # Get answer from PaperQA
            answer = self.docs.query(question)
            
            return {
                "answer": str(answer),
                "context": answer.context,
                "sources": [str(ref) for ref in answer.references]
            }
        except Exception as e:
            print(f"Error querying documents: {e}")
            return {
                "answer": "",
                "context": "Error retrieving information",
                "sources": []
            }

def create_paperqa_tool() -> Tool:
    """Create a LangChain Tool that wraps the PaperQA functionality."""
    rag = FitnessRAG()
    
    return Tool(
        name="fitness_knowledge_base",
        description="Retrieves relevant fitness information from local documents",
        func=rag.query_documents,
    )
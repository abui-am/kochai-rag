"""
FastAPI application for fitness knowledge retrieval.
"""
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv
import os

from rag.core import FitnessRAG

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="Fitness Knowledge Base",
    description="""
    An AI-powered fitness knowledge retrieval system using RAG (Retrieval-Augmented Generation).
    
    Features:
    - 🔍 Scientific paper-based knowledge retrieval
    - 🧠 GPT-4 powered response enhancement
    - 📚 Source citations for all information
    - 💪 Expert fitness guidance
    
    The system uses paper-qa for accurate knowledge retrieval from scientific papers.
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize RAG system
rag_system = FitnessRAG()

class QueryRequest(BaseModel):
    """Request model for the query endpoint."""
    question: str = Field(
        ...,
        description="The fitness-related question to ask",
        example="What are the benefits of compound exercises for muscle growth?"
    )

    class Config:
        schema_extra = {
            "example": {
                "question": "What are the benefits of compound exercises for muscle growth?"
            }
        }

class QueryResponse(BaseModel):
    """Response model for the query endpoint."""
    answer: str = Field(
        ...,
        description="The AI-generated answer based on scientific papers",
        example="Research indicates that compound exercises like squats and deadlifts..."
    )
    sources: List[str] = Field(
        ...,
        description="List of scientific papers used as sources",
        example=["Smith et al. 2023 - Effects of Compound Exercises..."]
    )
    context: str = Field(
        ...,
        description="The relevant context extracted from the papers",
        example="From the study by Smith et al.: Compound exercises showed significant..."
    )

    class Config:
        schema_extra = {
            "example": {
                "answer": "Research indicates that compound exercises like squats and deadlifts...",
                "sources": ["Smith et al. 2023 - Effects of Compound Exercises..."],
                "context": "From the study by Smith et al.: Compound exercises showed significant..."
            }
        }

class DocumentInfo(BaseModel):
    """Model for document information."""
    documents: List[str] = Field(
        ...,
        description="List of loaded document names",
        example=["study1.pdf", "research2.pdf"]
    )

    class Config:
        schema_extra = {
            "example": {
                "documents": ["study1.pdf", "research2.pdf"]
            }
        }

def get_rag_system() -> FitnessRAG:
    """Dependency to get RAG system instance."""
    return rag_system

# --------------------------
# LLM fallback (no-RAG answer)
# --------------------------

def _generate_llm_answer(question: str, model_name: Optional[str] = None) -> str:
    """Generate an answer directly from the LLM when RAG has insufficient info.

    Uses the OpenAI Chat Completions API via the official client.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set for LLM fallback")

    try:
        from openai import OpenAI
    except Exception as exc:  # pragma: no cover
        raise RuntimeError(f"OpenAI client not installed: {exc}")

    client = OpenAI(api_key=api_key)
    model = model_name or os.getenv("MODEL_NAME", "gpt-4o-mini")

    system_msg = (
        "You are an AI-powered fitness trainer assistant. Provide accurate, helpful, "
        "and safety-conscious advice. If you are not certain, be transparent."
    )

    completion = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user", "content": question},
        ],
        temperature=0.7,
    )

    return completion.choices[0].message.content.strip()

@app.get("/", tags=["Health Check"])
async def root():
    """Health check endpoint."""
    return {
        "status": "ok",
        "message": "Fitness Knowledge Base is running"
    }

@app.get(
    "/documents",
    response_model=DocumentInfo,
    tags=["Documents"],
    summary="Get loaded documents",
    description="Returns a list of all scientific papers loaded into the system."
)
async def get_documents(
    rag: FitnessRAG = Depends(get_rag_system)
) -> Dict[str, List[str]]:
    """Get list of loaded documents."""
    return {"documents": rag.get_loaded_documents()}

@app.post(
    "/query",
    response_model=QueryResponse,
    tags=["Query"],
    summary="Query the knowledge base",
    description="""
    Send a fitness-related question and receive an AI-generated response based on scientific papers.
    
    The system will:
    1. Search through scientific papers for relevant information
    2. Extract and process the information
    3. Generate a comprehensive response using GPT-4
    4. Include source citations
    
    Example questions:
    - "What are the benefits of compound exercises?"
    - "How does blood flow restriction training affect muscle growth?"
    - "What's the optimal rest period between sets for strength gains?"
    """
)
async def query(
    request: QueryRequest,
    rag: FitnessRAG = Depends(get_rag_system)
) -> Dict[str, Any]:
    """
    Process a query and return a response with sources.
    
    Args:
        request: QueryRequest containing the question
        rag: RAG system instance
        
    Returns:
        Dict containing the answer, sources, and context
        
    Raises:
        HTTPException: If there's an error processing the query
    """
    try:
        rag_result = await rag.query(request.question)

        answer_text = (rag_result.get("answer") or "").strip()
        sources = rag_result.get("sources") or []
        context = rag_result.get("context") or ""

        insufficient = (not answer_text) or ("insufficient information" in answer_text.lower()) or (len(sources) == 0)

        if insufficient:
            try:
                llm_answer = _generate_llm_answer(request.question)
                return {"answer": llm_answer, "sources": [], "context": ""}
            except Exception as e:  # If fallback fails, still return the RAG output
                # Provide transparency while not failing the request entirely
                fallback_note = f"[Fallback LLM unavailable: {e}]\n" if str(e) else ""
                return {"answer": fallback_note + answer_text, "sources": sources, "context": context}

        return rag_result

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing query: {str(e)}"
        )
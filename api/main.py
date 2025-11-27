"""
FastAPI application for fitness knowledge retrieval using simplified PaperQA workflow.
"""
import os
from typing import Annotated, List, Dict, Any, Optional, Union
from datetime import timedelta
from fastapi import FastAPI, HTTPException, Depends, status, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator
from dotenv import load_dotenv
from pydantic import BaseModel

from api.auth_utils import User, get_current_user, create_access_token, authenticate_user
from api.auth_utils import SECRET_KEY, ALGORITHM
import jwt
from paperqa.agents.models import AgentStatus
from api.database import (
    UserDB, init_db, create_user_from_registration, get_user_by_email,
    get_user_by_id, update_user_profile, update_user_preferences,
    complete_user_registration, get_user_stats, user_db_to_profile_response, user_db_to_model
)
from api.auth_models import (
    UserProfileUpdate, UserPreferences, UserRegistration, RegistrationResponse,
    ProfileResponse, UserStats, LoginCredentials, LoginResponse
)
from rag.agentic_workflow import create_fitness_knowledge_system, FitnessKnowledgeSystem
from rag.vanilla_workflow import create_vanilla_fitness_system, VanillaFitnessSystem
from rag import settings as rag_settings

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="Fitness Knowledge Base - PaperQA System",
    description="""
    An AI-powered fitness knowledge retrieval system using PaperQA for intelligent document analysis.
    
    Features:
    - 🧠 GPT-4 powered response generation
    - 📚 Source citations for all information
    - 💪 Expert fitness guidance with actionable recommendations
    - 🎯 Intelligent query processing and analysis
    - 🔍 Advanced document search and retrieval
    
    The system uses PaperQA for accurate knowledge retrieval and comprehensive analysis.
    """,
    version="2.0.0",
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

fitness_system: Optional[FitnessKnowledgeSystem] = None
vanilla_system: Optional[VanillaFitnessSystem] = None

@app.on_event("startup")
async def startup_event():
    """Initialize the fitness knowledge system and database on startup."""
    global fitness_system, vanilla_system
    try:
        await init_db()

        fitness_system = await create_fitness_knowledge_system(auto_index=True)
    except Exception as e:
        print(f"Failed to initialize RAG system: {e}")
        fitness_system = None

    try:
        vanilla_system = await create_vanilla_fitness_system()
    except Exception as e:
        print(f"Failed to initialize vanilla system: {e}")
        vanilla_system = None

class QueryRequest(BaseModel):
    """Request model for the query endpoint."""
    question: str = Field(
        ...,
        description="The fitness-related question to ask",
        example="What are the benefits of compound exercises for muscle growth?"
    )
    preferences: Optional[str] = Field(
        None,
        description="Optional inline preferences (will be merged with JWT/header/query params)"
    )

    class Config:
        schema_extra = {
            "example": {
                "question": "What are the benefits of compound exercises for muscle growth?",
                "preferences": "- Goal: muscle_gain\n- Equipment: resistance bands"
            }
        }

class PaperQASessionData(BaseModel):
    """Model for PaperQA session data."""
    id: Optional[str] = Field(None, description="Session ID")
    question: str = Field(..., description="The original question")
    answer: str = Field(..., description="The generated answer")
    raw_answer: Optional[str] = Field(None, description="Raw answer before formatting")
    formatted_answer: Optional[str] = Field(None, description="Formatted answer")
    context: Optional[str] = Field(None, description="Context used for the answer")
    references: Optional[List[str]] = Field(None, description="References used")
    citation: Optional[List[str]] = Field(None, description="Citations")
    contexts: Optional[List[Dict[str, Any]]] = Field(None, description="Context data")
    cost: Optional[float] = Field(None, description="Cost of the query")
    token_counts: Optional[Dict[str, List[int]]] = Field(None, description="Token usage")
    tool_history: Optional[List[List[str]]] = Field(None, description="Tool usage history")
    answer_reasoning: Optional[str] = Field(None, description="Reasoning for the answer")
    config_md5: Optional[str] = Field(None, description="Configuration hash")
    has_successful_answer: Optional[bool] = Field(None, description="Whether answer was successful")
    
    @field_validator('references', mode='before')
    @classmethod
    def validate_references(cls, v):
        """Convert string references to list if needed."""
        if v is None:
            return None
        if isinstance(v, str):
            if v.strip() == '':
                return []
            return [ref.strip() for ref in v.split('\n') if ref.strip()]
        if isinstance(v, list):
            return v
        return []
    
    @field_validator('citation', mode='before')
    @classmethod
    def validate_citation(cls, v):
        """Convert string citations to list if needed."""
        if v is None:
            return None
        if isinstance(v, str):
            if v.strip() == '':
                return []
            return [ref.strip() for ref in v.split('\n') if ref.strip()]
        if isinstance(v, list):
            return v
        return []

class QueryResponse(BaseModel):
    """Response model for the query endpoint with full PaperQA session data."""
    answer: Any = Field(
        ...,
        description="The AI-generated answer based on scientific papers",
        example="Research indicates that compound exercises like squats and deadlifts..."
    )
    sources:Any= Field(
        ...,
        description="List of scientific papers used as sources",
        example=["Smith et al. 2023 - Effects of Compound Exercises..."]
    )
    context: Any = Field(
        ...,
        description="The relevant context extracted from the papers",
        example="From the study by Smith et al.: Compound exercises showed significant..."
    )
    confidence: Any = Field(
        ...,
        description="Confidence level of the response",
        example="high"
    )
    query: Any = Field(
        ...,
        description="The original query that was asked",
        example="What are the benefits of compound exercises?"
    )
    status: Any = Field(
        ...,
        description="Status of the query processing",
        example="success"
    )
    enhancement_data:Any = Field(
        None,
        description="Additional enhancement data from RAG processing"
    )
    paperqa_session: Any= Field(
        None,
        description="Complete PaperQA session data"
    )

    class Config:
        schema_extra = {
            "example": {
                "answer": "Research indicates that compound exercises like squats and deadlifts...",
                "sources": ["Smith et al. 2023 - Effects of Compound Exercises..."],
                "context": "From the study by Smith et al.: Compound exercises showed significant...",
                "confidence": "high",
                "query": "What are the benefits of compound exercises?",
                "status": "success",
                "enhancement_data": "Additional RAG processing data...",
                "paperqa_session": {
                    "id": "session-uuid",
                    "question": "What are the benefits of compound exercises?",
                    "answer": "Research indicates that compound exercises...",
                    "cost": 0.0177,
                    "token_counts": {"gpt-4o-2024-11-20": [3255, 956]},
                    "tool_history": [["paper_search"], ["complete"], ["gen_answer"]]
                }
            }
        }

class VanillaQueryResponse(BaseModel):
    """Response model for the vanilla GPT-only endpoint."""
    answer: str = Field(..., description="Plain GPT answer without RAG enhancement")
    model: str = Field(..., description="OpenAI model used to generate the answer")
    usage: Dict[str, Any] = Field(..., description="Token usage metadata")
    query: str = Field(..., description="Original question")
    status: str = Field(..., description="Processing status, e.g., success")
    preferences: Optional[str] = Field(None, description="User preferences applied, if any")

    class Config:
        schema_extra = {
            "example": {
                "answer": "Latihan compound kayak squat membantu kamu pakai banyak otot sekaligus...",
                "model": "gpt-4o-mini",
                "usage": {"input_tokens": 315, "output_tokens": 185, "total_tokens": 500},
                "query": "Apa manfaat compound exercise buat muscle growth?",
                "status": "success",
                "preferences": "- Name: Raka\n- Fitness goals: muscle_gain"
            }
        }

class SystemStatus(BaseModel):
    """Model for system status information."""
    system_status: str = Field(..., description="Status of the fitness knowledge system")
    documents_loaded: bool = Field(..., description="Whether documents are loaded")
    total_documents: int = Field(..., description="Total documents in the system")
    system_health: str = Field(..., description="Overall system health status")
    index_built: bool = Field(..., description="Whether the PaperQA index is built")
    auto_indexing: bool = Field(..., description="Whether auto-indexing is enabled")

async def get_fitness_system() -> FitnessKnowledgeSystem:
    """Dependency to get fitness knowledge system instance."""
    global fitness_system
    if fitness_system is None:
        fitness_system = await create_fitness_knowledge_system(auto_index=True)
    return fitness_system


def _extract_user_id_from_request(request: Request) -> Optional[str]:
    """Extract user_id from Authorization header if present and valid.

    Returns None if header is missing/invalid. This keeps the endpoint usable without auth.
    """
    try:
        auth_header = request.headers.get("authorization") or request.headers.get("Authorization")
        if not auth_header or not auth_header.lower().startswith("bearer "):
            return None
        token = auth_header.split(" ", 1)[1].strip()
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub")
    except Exception:
        return None


def _format_user_preferences(user_db: UserDB) -> Optional[str]:
    """Create a compact, human-readable preferences block from UserDB fields."""

    # Collect only populated preferences
    prefs: list[str] = []
    prefs.append(f"- Name: {user_db.name}")
    prefs.append(f"- Fitness goals: {', '.join(user_db.fitness_goals)}")
    prefs.append(f"- Experience level: {user_db.experience_level}")
    prefs.append(f"- Preferred workout types: {', '.join(user_db.preferred_workout_types)}")
    prefs.append(f"- Workout frequency: {user_db.workout_frequency}")
    prefs.append(f"- Available equipment: {', '.join(user_db.available_equipment)}")
    prefs.append(f"- Dietary restrictions: {', '.join(user_db.dietary_restrictions)}")
    prefs.append(f"- Timezone: {user_db.timezone}")
    return "\n".join(prefs)


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

@app.get("/", tags=["Health Check"])
async def root():
    """Health check endpoint."""
    return {
        "status": "ok",
        "message": "Fitness Knowledge Base - PaperQA System is running",
        "version": "2.0.0",
        "features": ["PaperQA Integration", "Document Analysis", "AI-Powered Responses"],
        "system_type": "simplified_paperqa"
    }

@app.get(
    "/system/status",
    response_model=SystemStatus,
    tags=["System"],
    summary="Get system status",
    description="Returns the status of the fitness knowledge system."
)
async def get_system_status() -> Dict[str, Any]:
    """Get system status."""
    try:
        if fitness_system is None:
            return {
                "system_status": "not_initialized",
                "documents_loaded": False,
                "total_documents": 0,
                "system_health": "initializing"
            }
        
        # Get document count and index status
        doc_count = fitness_system.get_document_count()
        index_built = getattr(fitness_system, 'index_built', False)
        auto_indexing = getattr(fitness_system, 'auto_index', False)
        
        return {
            "system_status": "ready",
            "documents_loaded": doc_count > 0,
            "total_documents": doc_count,
            "system_health": "healthy" if doc_count > 0 else "no_documents",
            "index_built": index_built,
            "auto_indexing": auto_indexing
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting system status: {str(e)}"
        )

@app.post(
    "/query",
    response_model=QueryResponse,
    tags=["Query"],
    summary="Query the knowledge base using PaperQA",
    description="""
    Send a fitness-related question and receive an AI-generated response using PaperQA.
    
    The system uses PaperQA for intelligent document analysis that includes:
    1. **Document Retrieval**: Advanced search through scientific papers
    2. **Context Analysis**: Intelligent extraction of relevant information
    3. **Answer Generation**: GPT-4 powered response creation
    4. **Source Citation**: Proper attribution to scientific sources
    
    All queries are processed through PaperQA for consistent, high-quality responses.
    
    Example questions:
    - "What are the benefits of compound exercises?"
    - "How should I design a workout program for muscle building with limited time?"
    - "What's the optimal nutrition plan for muscle recovery?"
    - "How can I prevent injuries during strength training?"
    """
)
async def query(
    request: QueryRequest,
    raw_request: Request
) -> Dict[str, Any]:
    """
    Process a query using the PaperQA system.
    
    Args:
        request: QueryRequest containing the question
        
    Returns:
        Dict containing the answer with sources and context
        
    Raises:
        HTTPException: If there's an error processing the query
    """
    try:
        # Get the fitness knowledge system instance
        system = await get_fitness_system()
        
        # Optionally fetch user preferences from token; pass to agent_prompt only
        db_prefs: Optional[str] = None
        user_id = _extract_user_id_from_request(raw_request)
        if user_id:
            try:
                db_user = await get_user_by_id(user_id)
                prefs_block = _format_user_preferences(db_user)
                if prefs_block:
                    db_prefs = prefs_block
            except Exception:
                # Non-fatal; continue without preferences if anything goes wrong
                pass

        agent_prefs = db_prefs;
        # Execute the query using PaperQA
        result = await system.query(request.question, preferences=agent_prefs)

        # Check if query was successful and has an answer
        if result.status != AgentStatus.FAIL and result.session.raw_answer:
            return {
                "answer": result.session.raw_answer,
                "context": result.session.context,
                "confidence": result.session.graded_answer,
                "query": result.session.question,
                "status": result.session.has_successful_answer,
                "enhancement_data": result.session.answer_reasoning,
                "paperqa_session": result.session,
                "sources" : result.bibtex
            }

        else:
            # Handle failed or empty response
            error_msg = f"Query failed with status: {result.status}"
            if result.session.raw_answer:
                error_msg += f" - Response: {result.session.raw_answer}"
            raise HTTPException(
                status_code=500,
                detail=f"Query processing failed: {error_msg}"
            )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing query: {str(e)}"
        )


def _merge_preferences(*blocks: Optional[str]) -> Optional[str]:
    """Merge multiple preference blocks into one."""
    merged = [block.strip() for block in blocks if block and block.strip()]
    if not merged:
        return None
    return "\n".join(merged)


async def _extract_vanilla_payload(raw_request: Request) -> str:
    """Parse the vanilla endpoint payload. Only JSON objects with a `text` field are allowed."""
    import json

    body_bytes = await raw_request.body()
    if not body_bytes:
        raise HTTPException(
            status_code=422,
            detail="Payload is required. Send a JSON object like {'text': '...'}."
        )

    try:
        data = json.loads(body_bytes.decode("utf-8"))
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid JSON payload: {exc}"
        ) from exc

    if not isinstance(data, dict):
        raise HTTPException(
            status_code=400,
            detail="Payload must be a JSON object with a `text` property."
        )

    question = str(data.get("text") or "").strip()
    if not question:
        raise HTTPException(
            status_code=422,
            detail="The `text` field cannot be empty."
        )

    return question


@app.post(
    "/query/vanilla",
    response_model=VanillaQueryResponse,
    tags=["Query"],
    summary="Ask GPT directly without RAG",
    description="""
    Send a fitness question to the base GPT model without PaperQA retrieval.

    Send a minimal JSON body containing a `text` field. The API will automatically
    apply any stored user preferences from the JWT token, mirroring the RAG endpoint.
    """
)
async def query_vanilla(
    raw_request: Request
) -> Dict[str, Any]:
    """Process a GPT-only query for comparison against RAG responses."""
    if vanilla_system is None:
        raise HTTPException(
            status_code=503,
            detail="Vanilla GPT system not ready. Check OPENAI_API_KEY configuration."
        )

    try:
        question_text = await _extract_vanilla_payload(raw_request)
        user_id = _extract_user_id_from_request(raw_request)

        # Get user preferences if user_id is available
        preferences = None
        if user_id:
            try:
                db_user = await get_user_by_id(user_id)
                prefs_block = _format_user_preferences(db_user)
                if prefs_block:
                    preferences = prefs_block
            except Exception:
                pass

        result = await vanilla_system.query(question_text, preferences)
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing vanilla query: {str(e)}"
        )

@app.get(
    "/documents",
    tags=["Documents"],
    summary="Get document count",
    description="Returns the number of documents loaded into the system."
)
async def get_document_count() -> Dict[str, Any]:
    """Get document count."""
    try:
        if fitness_system is None:
            return {"documents": 0, "message": "System not initialized"}
        count = fitness_system.get_document_count()
        return {"documents": count, "message": f"Found {count} documents"}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting document count: {str(e)}"
        )

# ===== AUTHENTICATION ENDPOINTS =====

@app.post(
    "/login",
    response_model=LoginResponse,
    tags=["Authentication"],
    summary="Login with email and password",
    description="""
    Authenticate a user with email and password.

    Returns a JWT access token that can be used to access protected endpoints.
    The token expires after 30 minutes.
    """
)
async def login(credentials: LoginCredentials) -> Dict[str, Any]:
    """Login with email and password."""
    try:
        user = await authenticate_user(credentials.email, credentials.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        access_token_expires = timedelta(minutes=10000)
        access_token = create_access_token(
            data={"sub": user.id, "email": user.email}, expires_delta=access_token_expires
        )

        return {
            "message": "Login successful",
            "user": user,
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": 10000 
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Login failed: {str(e)}"
        )

@app.get("/users/me")
async def read_users_me(current_user: Annotated[User, Depends(get_current_user)]):
    return current_user


# ===== REGISTRATION AND PROFILE MANAGEMENT ENDPOINTS =====

@app.post(
    "/register",
    response_model=LoginResponse,
    tags=["Registration"],
    summary="Register new user account",
    description="""
    Register a new user account with the fitness knowledge base.

    This endpoint allows users to:
    - Create a new account with email and full name
    - Set initial profile information (bio, location, website)
    - Set fitness preferences and goals
    - Receive an authentication token for immediate use

    Required fields: email, name
    Optional fields: profile, preferences

    No prior authentication is required - this creates a new user account.
    """
)
async def register_user(
    registration_data: UserRegistration
) -> Dict[str, Any]:
    """Register a new user account."""
    try:
        # Check if user with this email already exists
        existing_user = await get_user_by_email(registration_data.email)
        if existing_user:
            raise HTTPException(
                status_code=409,
                detail="User with this email already exists"
            )

        # Create new user account
        registration_dict = {
            'email': registration_data.email,
            'name': registration_data.name,
            'password': registration_data.password,
            'profile': registration_data.profile,
            'preferences': registration_data.preferences,
        }
        new_user = await create_user_from_registration(registration_dict)

        new_user = await complete_user_registration(new_user.id)
        access_token_expires = timedelta(minutes=10000)
        access_token = create_access_token(
            data={"sub": new_user.id, "email": new_user.email}, expires_delta=access_token_expires
        )

        return {
            "message": "Registration completed successfully",
            "user": user_db_to_model(new_user),
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": 10000
        }

    except HTTPException:
        raise
    except Exception as e:
        if "UNIQUE constraint failed" in str(e) or "already exists" in str(e).lower():
            raise HTTPException(
                status_code=409,
                detail="User with this email already exists"
            )
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Registration failed: {str(e)}"
            )


@app.get(
    "/profile",
    response_model=ProfileResponse,
    tags=["Profile"],
    summary="Get user profile",
    description="Get the current user's profile information, preferences, and registration status."
)
async def get_user_profile(
    current_user: Annotated[User, Depends(get_current_user)]
) -> Dict[str, Any]:
    """Get user profile with preferences and registration status."""
    try:
        db_user = await get_user_by_id(current_user.id)
        if not db_user:
            raise HTTPException(
                status_code=404,
                detail="User not found"
            )

        return user_db_to_profile_response(db_user)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get profile: {str(e)}"
        )


@app.put(
    "/profile",
    response_model=ProfileResponse,
    tags=["Profile"],
    summary="Update user profile",
    description="Update the current user's profile information such as bio, location, and website."
)
async def update_user_profile_endpoint(
    profile_update: UserProfileUpdate,
    current_user: Annotated[User, Depends(get_current_user)]
) -> Dict[str, Any]:
    """Update user profile information."""
    try:
        profile_data = profile_update.dict(exclude_unset=True)
        updated_user = await update_user_profile(current_user.id, profile_data)

        if not updated_user:
            raise HTTPException(
                status_code=404,
                detail="User not found"
            )

        return user_db_to_profile_response(updated_user)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Profile update failed: {str(e)}"
        )


@app.put(
    "/preferences",
    response_model=ProfileResponse,
    tags=["Preferences"],
    summary="Update user preferences",
    description="""
    Update the current user's fitness preferences and settings.

    This includes:
    - Fitness goals (muscle_gain, weight_loss, etc.)
    - Experience level (beginner, intermediate, advanced)
    - Preferred workout types and frequency
    - Available equipment and dietary restrictions
    - Notification and language preferences
    """
)
async def update_user_preferences_endpoint(
    preferences: UserPreferences,
    current_user: Annotated[User, Depends(get_current_user)]
) -> Dict[str, Any]:
    """Update user preferences."""
    try:
        preferences_data = preferences.dict(exclude_unset=True)
        updated_user = await update_user_preferences(current_user.id, preferences_data)

        if not updated_user:
            raise HTTPException(
                status_code=404,
                detail="User not found"
            )

        return user_db_to_profile_response(updated_user)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Preferences update failed: {str(e)}"
        )


@app.get(
    "/stats",
    response_model=UserStats,
    tags=["Statistics"],
    summary="Get user statistics",
    description="Get the current user's activity statistics and account information."
)
async def get_user_stats_endpoint(
    current_user: Annotated[User, Depends(get_current_user)]
) -> Dict[str, Any]:
    """Get user statistics and activity data."""
    try:
        stats = await get_user_stats(current_user.id)

        if not stats:
            raise HTTPException(
                status_code=404,
                detail="User statistics not found"
            )
        stats["account_created"] = current_user.created_at

        return stats

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get statistics: {str(e)}"
        )
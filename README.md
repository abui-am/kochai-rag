# Fitness RAG

A comprehensive AI-powered fitness knowledge system combining Retrieval-Augmented Generation (RAG) with PaperQA for intelligent document analysis and personalized fitness guidance.

## ✨ Features

- 🤖 **AI-Powered Responses**: GPT-4 powered fitness guidance with scientific accuracy
- 📚 **Research Integration**: PaperQA-powered document analysis and citation tracking
- 🔐 **User Authentication**: Secure user registration, login, and profile management
- 🎯 **Personalized Recommendations**: User preferences and fitness goals integration
- 📊 **System Monitoring**: Real-time system status and document indexing
- 🧪 **Hybrid Approach**: Combines vanilla LLM with RAG for optimal responses
- 📈 **Performance Evaluation**: RAGAS-powered evaluation and metrics
- 🔄 **Auto-indexing**: Automatic document processing and indexing

## Setup

### Prerequisites

- Python 3.11+
- OpenAI API key
- SQLite database (default) or PostgreSQL

### Quick Start

1. **Clone and setup environment:**

```bash
git clone <repository-url>
cd fitness-rag
python3.11 -m venv venv
source venv/bin/activate  # On Unix/macOS
# or
.\venv\Scripts\activate   # On Windows
```

2. **Install dependencies:**

```bash
pip install -r requirements.txt
```

3. **Configure environment:**

Create a `.env` file in the project root:

```bash
# Required
OPENAI_API_KEY=your_openai_api_key_here

# Optional - API Server
API_HOST=0.0.0.0
API_PORT=8000

# Optional - Database (SQLite by default)
DATABASE_URL=sqlite+aiosqlite:///./fitness_rag.db

# Optional - RAGAS Evaluation
RAGAS_JUDGE_MODEL=gpt-4o-mini

# Optional - Vanilla LLM settings
VANILLA_TEMPERATURE=0.2
```

### Database Setup

The system uses SQLite by default. The database will be automatically created on first run. For production, consider PostgreSQL:

```bash
# For PostgreSQL
DATABASE_URL=postgresql+asyncpg://user:password@localhost/fitness_rag
```

## 📁 Project Structure

```
fitness-rag/
├── api/                         # FastAPI application
│   ├── main.py                  # Main API endpoints and routing
│   ├── auth_utils.py            # Authentication utilities
│   ├── auth_models.py           # Authentication data models
│   └── database.py              # Database operations and models
├── rag/                         # RAG system core
│   ├── agentic_workflow.py      # PaperQA integration and knowledge system
│   ├── vanilla_workflow.py      # Vanilla (non-RAG) query system
│   ├── utils.py                 # Shared utility functions
│   ├── settings.py              # Configuration and model settings
│   └── evaluation/              # Evaluation framework
│       ├── preferences.py       # User preference handling
│       └── ragas/               # RAGAS evaluation
│           ├── run_eval.py      # RAG evaluation runner
│           ├── run_eval_vanilla.py # Vanilla evaluation runner
│           ├── adapters.py      # RAGAS adapters
│           └── dataset_loader.py # Dataset loading utilities
├── config/                      # Configuration files
│   └── user_preferences_dummy.json # Default user preferences
├── data/                        # Data and evaluation
│   ├── sources/                 # Document sources
│   │   └── processed/           # Processed documents
│   └── evaluation/              # Evaluation datasets and results
│       ├── dataset.json         # Evaluation questions
│       ├── dataset-preferenced.json # Personalized evaluation
│       └── results/             # Evaluation outputs
├── docs/                        # Documentation
│   ├── CACHE_GUIDE.md           # Caching documentation
│   ├── GOOGLE_AUTH_SETUP.md     # Google Auth setup guide
│   ├── IMPLEMENTATION_SUMMARY.md # Implementation details
│   └── VERIFICATION_REPORT.md   # Verification reports
├── tests/                       # Unit tests
│   └── test_preferences_loader.py # Preferences testing
├── requirements.txt             # Python dependencies (10 core packages)
├── run.py                       # Application entry point
├── populate_dataset.py          # Dataset population script
├── evaluation_dataset*.json     # Generated evaluation datasets
└── README.md                    # This file
```

## 🗂️ Data Management

The system uses PaperQA for intelligent document processing and RAG capabilities:

### Document Management

- **Document Storage**: Place fitness research documents (PDFs, TXTs) in `data/sources/`
- **Automatic Processing**: Documents are automatically indexed and processed on system startup
- **Smart Chunking**: Intelligent document segmentation for optimal retrieval
- **Citation Tracking**: Automatic source attribution and reference management

### Document Preparation

```bash
# Place your documents in the sources directory
cp your_fitness_papers.pdf data/sources/
cp research_articles.txt data/sources/

# The system will automatically index them on first query
```

## 🧠 Hybrid Intelligence: Combining LLM + RAG

The system employs a sophisticated hybrid approach that intelligently combines:

### Core Architecture

- **Vanilla LLM Base**: Direct GPT queries for conversational, engaging responses in Indonesian
- **RAG Enhancement**: Adds scientific accuracy through document retrieval and citation
- **Intelligent Merging**: Seamlessly integrates research facts into natural conversation
- **Modular Design**: Separate vanilla and RAG workflows for flexible evaluation and comparison

### Key Benefits

- 🎯 **Conversational Flow**: Maintains natural dialogue while adding scientific depth
- 📚 **Evidence-Based**: All claims backed by research paper citations
- 🔄 **Fallback Ready**: Works with or without document context
- 🎭 **Personalized**: Adapts to user preferences and fitness goals
- 📖 **Transparent**: Clear source attribution for credibility

### Response Characteristics

- **Language**: Indonesian (Bahasa Indonesia)
- **Tone**: Supportive, certified fitness coach
- **Content**: Evidence-based with actionable recommendations
- **Sources**: Automatic citation of research papers

## 🚀 Usage

### Starting the API Server

```bash
python run.py
```

The API will be available at `http://localhost:8000` with automatic API documentation at `http://localhost:8000/docs`.

### API Endpoints

#### Health & System Status

- `GET /` - Health check
- `GET /system/status` - System status and document indexing info

#### Authentication

- `POST /login` - User login (returns JWT token)
- `POST /register` - User registration
- `GET /users/me` - Get current user profile (requires auth)

#### Query Endpoints

- `POST /query` - Main RAG query with PaperQA document analysis and scientific citations
- `POST /query/vanilla` - Direct GPT query without RAG (for baseline comparison)

### Example API Usage

#### Health Check

```bash
curl http://localhost:8000/
```

#### User Registration

```bash
curl -X POST http://localhost:8000/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "name": "Fitness User",
    "password": "securepassword"
  }'
```

#### Login

```bash
curl -X POST http://localhost:8000/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepassword"
  }'
```

#### RAG Query (with authentication)

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "text": "What are the benefits of compound exercises for muscle growth?"
  }'
```

#### Vanilla GPT Query (comparison)

```bash
curl -X POST http://localhost:8000/query/vanilla \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "text": "What are the benefits of compound exercises for muscle growth?"
  }'
```

## 📊 Evaluation & Testing

### RAGAS Evaluation Framework

Evaluate your RAG system's performance using the comprehensive RAGAS evaluation suite:

#### Quick Evaluation

```bash
# Run RAG evaluation with default settings
python -m rag.evaluation.ragas.run_eval --use-default-preferences --dataset data/evaluation/dataset-preferenced.json --max-samples 50

# Run vanilla (non-RAG) evaluation
python -m rag.evaluation.ragas.run_eval_vanilla --use-default-preferences --dataset data/evaluation/dataset-preferenced-vanilla.json --max-samples 50
```

#### Advanced Evaluation Options

```bash
# RAG evaluation with custom judge model
python -m rag.evaluation.ragas.run_eval \
  --dataset data/evaluation/dataset.json \
  --model gpt-4o \
  --max-samples 100 \
  --use-default-preferences

# Vanilla evaluation with custom judge model
python -m rag.evaluation.ragas.run_eval_vanilla \
  --dataset data/evaluation/dataset.json \
  --model gpt-4o \
  --max-samples 100 \
  --use-default-preferences

# With custom document directory (RAG only)
python -m rag.evaluation.ragas.run_eval \
  --dataset data/evaluation/dataset.json \
  --docs-dir ./custom_docs/ \
  --save-dir ./evaluation_results/
```

#### Evaluation Types

The system supports two evaluation modes:

- **RAG Evaluation** (`run_eval.py`): Tests the full RAG pipeline with document retrieval, context analysis, and scientific citations. Uses multiple metrics (Context Relevance, Faithfulness, Answer Relevancy, etc.)

- **Vanilla Evaluation** (`run_eval_vanilla.py`): Tests direct LLM responses without document retrieval. Uses only Answer Relevancy metric for focused evaluation of conversational quality.

#### Evaluation Outputs

- `data/evaluation/results/<timestamp>/per_sample.csv` - Individual sample results
- `data/evaluation/results/<timestamp>/aggregate.json` - Overall metrics and scores
- `vanilla_evaluation_dataset.json` - Generated vanilla evaluation dataset
- `vanilla_settings_report_<timestamp>.json` - Vanilla evaluation configuration and results

### Dataset Management

#### Generate Evaluation Datasets

```bash
# Basic RAG dataset without preferences
python populate_dataset.py

# Vanilla (non-RAG) dataset without preferences
python populate_dataset.py --vanilla

# RAG dataset with custom preferences
python populate_dataset.py --preferences-text "- Goal: muscle_gain\n- Equipment: resistance bands"

# Vanilla dataset with custom preferences
python populate_dataset.py --vanilla --preferences-text "- Goal: muscle_gain\n- Equipment: resistance bands"

# RAG dataset with default preferences
python populate_dataset.py --use-default-preferences

# Vanilla dataset with default preferences
python populate_dataset.py --vanilla --use-default-preferences
```

#### Dataset Format

The system supports two dataset formats:

**RAG Dataset Format:**

```json
[
  {
    "question": "What are the benefits of compound exercises?",
    "ground_truth": "Compound exercises work multiple muscle groups simultaneously...",
    "contexts": ["Context 1...", "Context 2..."],
    "context_ids": ["doc1.pdf", "doc2.pdf"]
  }
]
```

**Vanilla Dataset Format:**

```json
[
  {
    "question": "What are the benefits of compound exercises?",
    "ground_truth": "Compound exercises work multiple muscle groups simultaneously..."
  }
]
```

Vanilla datasets are simpler with only question and ground_truth fields.

### Testing Scripts

#### Unit Tests

```bash
# Run preference loader tests
python -m pytest tests/test_preferences_loader.py -v
```

#### Integration Testing

```bash
# Test API endpoints
curl http://localhost:8000/

# Test system status
curl http://localhost:8000/system/status
```

## 🔧 Development

### Code Quality

- **Linting**: Uses Ruff for fast Python linting
- **Testing**: Pytest framework for unit and integration tests
- **Type Hints**: Full type annotation coverage

### Dependencies

The project maintains a minimal, curated dependency list with only 10 core packages:

- `fastapi` - Web framework
- `pydantic` - Data validation
- `sqlalchemy` - Database ORM
- `openai` - OpenAI API client
- `paper-qa` - Document analysis
- `passlib` - Password hashing
- `PyJWT` - JWT token handling
- `python-dotenv` - Environment management
- `ragas` - Evaluation framework
- `uvicorn` - ASGI server

## 🚀 Deployment

### Production Setup

```bash
# Use production database
DATABASE_URL=postgresql+asyncpg://user:password@host:port/database

# Set secure JWT secret
JWT_SECRET_KEY=your-secure-random-secret-here

# Configure for production
API_HOST=0.0.0.0
API_PORT=8000
```

### Docker Deployment (Future)

```bash
# Planned: Docker support coming soon
docker build -t fitness-rag .
docker run -p 8000:8000 fitness-rag
```

## 🔍 Troubleshooting

### Common Issues

**Database Connection Errors**

```bash
# Check database URL format
DATABASE_URL=sqlite+aiosqlite:///./fitness_rag.db  # SQLite
DATABASE_URL=postgresql+asyncpg://user:pass@host/db  # PostgreSQL
```

**OpenAI API Errors**

```bash
# Verify API key
echo $OPENAI_API_KEY
# Should start with 'sk-'
```

**Document Indexing Issues**

```bash
# Check document directory permissions
ls -la data/sources/

# Verify document formats (PDF/TXT supported)
file data/sources/your_document.pdf
```

### Debug Mode

```bash
# Enable debug logging
LOG_LEVEL=DEBUG python run.py
```

## 📚 Documentation

Additional documentation available in `docs/`:

- `CACHE_GUIDE.md` - Document caching strategies
- `GOOGLE_AUTH_SETUP.md` - Authentication setup
- `IMPLEMENTATION_SUMMARY.md` - Technical implementation details
- `VERIFICATION_REPORT.md` - System verification reports

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Run evaluation suite
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

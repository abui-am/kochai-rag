# Kochai RAG

An AI-powered fitness knowledge API that combines [PaperQA](https://github.com/Future-House/paper-qa) retrieval with a vanilla GPT baseline for evidence-based, personalized fitness guidance. Responses are tuned for conversational Bahasa Indonesia with research citations.

## Features

- **PaperQA RAG pipeline** — document retrieval, evidence summarization, and source citations
- **Vanilla GPT baseline** — direct LLM answers for comparison and evaluation
- **User accounts** — registration, JWT auth, and stored fitness preferences
- **Personalization** — preferences injected into RAG and vanilla prompts when authenticated
- **RAGAS evaluation** — automated metrics for RAG and vanilla answer quality
- **Auto-indexing** — documents in `data/sources/processed/` are indexed on startup

## Quick start

### Prerequisites

- Python 3.11+
- OpenAI API key

### Setup

```bash
git clone https://github.com/abui-am/kochai-rag.git
cd kochai-rag
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Copy `.env.template` to `.env` and set your API key:

```bash
cp .env.template .env
```

```env
OPENAI_API_KEY=your_openai_api_key_here
API_HOST=0.0.0.0
API_PORT=8000
LOG_LEVEL=INFO
```

Optional settings:

```env
DATABASE_URL=sqlite+aiosqlite:///./fitness_rag.db
RAGAS_JUDGE_MODEL=gpt-4o-mini
VANILLA_TEMPERATURE=0.2
JWT_SECRET_KEY=your-secure-random-secret
```

SQLite is used by default and is created automatically on first run. For PostgreSQL:

```env
DATABASE_URL=postgresql+asyncpg://user:password@localhost/fitness_rag
```

### Run the server

```bash
python run.py
```

- API: `http://localhost:8000`
- Interactive docs: `http://localhost:8000/docs`

## Project structure

```
kochai-rag/
├── api/                    # FastAPI app, auth, database
├── rag/
│   ├── agentic_workflow.py # PaperQA RAG pipeline
│   ├── vanilla_workflow.py # GPT-only baseline
│   ├── settings.py         # Model and retrieval config
│   └── evaluation/         # RAGAS eval and preferences
├── config/                 # Default user preference profiles
├── data/
│   ├── sources/processed/  # PDF/TXT documents for RAG
│   └── evaluation/         # Datasets and eval results
├── docs/                   # Additional documentation
├── tests/
├── run.py                  # Server entry point
└── populate_dataset.py     # Generate evaluation datasets
```

## Documents

Place fitness research PDFs or text files in `data/sources/processed/`. The RAG system indexes them automatically on startup.

```bash
cp your_paper.pdf data/sources/processed/
```

Check indexing status:

```bash
curl http://localhost:8000/system/status
curl http://localhost:8000/documents
```

## Architecture

The system runs two parallel query paths:

| Path | Endpoint | Description |
|------|----------|-------------|
| RAG | `POST /query` | PaperQA retrieval + GPT answer with citations |
| Vanilla | `POST /query/vanilla` | Direct GPT answer without document retrieval |

When a valid JWT is provided, stored user preferences (goals, equipment, experience level, etc.) are merged into the prompt. Both paths respond in conversational Bahasa Indonesia with a certified-coach tone.

Model and retrieval settings live in `rag/settings.py` (LLM choice, evidence count, embedding model, temperature, etc.).

## API reference

### Health and system

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/` | Health check |
| `GET` | `/system/status` | Index and document status |
| `GET` | `/documents` | Document count |

### Authentication and profile

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `POST` | `/register` | — | Create account, returns JWT |
| `POST` | `/login` | — | Login, returns JWT |
| `GET` | `/users/me` | JWT | Current user |
| `GET` | `/profile` | JWT | Full profile |
| `PUT` | `/profile` | JWT | Update profile |
| `PUT` | `/preferences` | JWT | Update fitness preferences |
| `GET` | `/stats` | JWT | User activity stats |

### Query

**RAG query** — body uses `question`:

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{"question": "Apa manfaat latihan compound untuk pertumbuhan otot?"}'
```

**Vanilla query** — body uses `text`:

```bash
curl -X POST http://localhost:8000/query/vanilla \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{"text": "Apa manfaat latihan compound untuk pertumbuhan otot?"}'
```

Auth is optional on query endpoints; when omitted, queries run without stored preferences.

## Evaluation

### Generate datasets

```bash
# RAG dataset with default preferences
python populate_dataset.py --use-default-preferences

# Vanilla dataset
python populate_dataset.py --vanilla --use-default-preferences

# Custom preferences
python populate_dataset.py --preferences-text "- Goal: muscle_gain\n- Equipment: resistance bands"
```

### Run RAGAS

```bash
# RAG evaluation
python -m rag.evaluation.ragas.run_eval \
  --use-default-preferences \
  --dataset data/evaluation/dataset-preferenced.json \
  --max-samples 50

# Vanilla evaluation
python -m rag.evaluation.ragas.run_eval_vanilla \
  --use-default-preferences \
  --dataset data/evaluation/dataset-preferenced-vanilla.json \
  --max-samples 50
```

Results are written to `data/evaluation/results/<timestamp>/` (`per_sample.csv`, `aggregate.json`).

### Tests

```bash
python -m pytest tests/ -v
```

## Configuration

| Variable | Default | Purpose |
|----------|---------|---------|
| `OPENAI_API_KEY` | — | Required for all LLM calls |
| `API_HOST` | `0.0.0.0` | Server bind address |
| `API_PORT` | `8000` | Server port |
| `DATABASE_URL` | SQLite file | Async SQLAlchemy connection |
| `JWT_SECRET_KEY` | dev default | JWT signing secret |
| `RAGAS_JUDGE_MODEL` | `gpt-4o-mini` | Judge model for evaluation |
| `VANILLA_TEMPERATURE` | `0.2` | Vanilla LLM temperature |
| `LOG_LEVEL` | `INFO` | Logging verbosity |

## Troubleshooting

**RAG system not initialized** — confirm `OPENAI_API_KEY` is set and restart the server.

**No documents indexed** — verify files exist in `data/sources/processed/` and check `/system/status`.

**Database errors** — SQLite uses `sqlite+aiosqlite:///./fitness_rag.db`; PostgreSQL uses `postgresql+asyncpg://...`.

**Debug logging**:

```bash
LOG_LEVEL=DEBUG python run.py
```

## Documentation

- [Google Auth setup](docs/GOOGLE_AUTH_SETUP.md) — OAuth2 integration guide

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests where relevant
4. Run the evaluation suite
5. Open a pull request

# Fitness RAG

A RAG (Retrieval-Augmented Generation) system for fitness-related research papers and content.

## Setup

1. Create a Python virtual environment:

```bash
python3.11 -m venv venv
source venv/bin/activate  # On Unix/macOS
# or
.\venv\Scripts\activate  # On Windows
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Set up environment variables:
   - Copy `.env.template` to `.env`
   - Edit `.env` and add your OpenAI API key and other configurations

```bash
cp .env.template .env
# Edit .env with your preferred editor
```

4. Required environment variables:
   - `OPENAI_API_KEY`: Your OpenAI API key
   - `MODEL_NAME`: OpenAI model to use (default: gpt-4-turbo-preview)
   - `API_HOST`: Host to run the API on (default: 0.0.0.0)
   - `API_PORT`: Port to run the API on (default: 8000)
   - `LOG_LEVEL`: Logging level (default: INFO)
   - `VANILLA_MODEL_NAME`: (optional) GPT model for the comparison endpoint (default: gpt-4o-mini)
   - `VANILLA_TEMPERATURE`: (optional) Generation temperature for `/query/vanilla` (default: 0.2)

## 📁 Project Structure

```
fitness-rag/
├── config/
│   └── agentic_config.yaml      # Agentic workflow configurations
├── src/
│   ├── models/                  # Model architectures
│   ├── data/                    # Data loading and processing
│   ├── training/                # Training loops and utilities
│   ├── inference/               # Inference pipelines
│   └── utils/                   # Helper functions
├── rag/
│   └── agentic_workflow.py     # Core agentic workflow system
├── gradio_app/                  # Gradio web interface
├── notebooks/                   # Jupyter notebooks for experiments
├── scripts/                     # Training and inference scripts
├── tests/                       # Unit tests
├── data/                        # Document storage (any directory with PDFs/TXTs)
├── requirements.txt             # Python dependencies
├── start_api.py                 # API startup script
└── README.md                    # This file
```

## 🗂️ Data Management

The system uses PaperQA2 for automatic document processing and indexing:

- **Document Storage**: Place your fitness research documents (PDFs, TXTs) in any directory
- **Automatic Indexing**: PaperQA2 automatically indexes documents on first query
- **Smart Processing**: Intelligent chunking and embedding for optimal retrieval
- **Citation Tracking**: Automatic source citation and reference management

## 🚀 Hybrid Approach: Vanilla LLM (Base) + RAG (Enhancement)

The system now uses a **hybrid approach** that uses vanilla LLM as the foundation and RAG as enhancement:

### How It Works

1. **Vanilla LLM Base**: First, the system generates a conversational, friendly BASE response using the base LLM
2. **RAG Data Enhancement**: Then, it retrieves specific, factual information from your fitness research documents
3. **Intelligent Merging**: Finally, it intelligently merges both into ONE cohesive answer, weaving research facts naturally into the conversational tone

### Benefits

- **🎯 Strong Foundation**: Vanilla LLM provides conversational, engaging base responses
- **📚 Enhanced Details**: RAG adds specific, factual information from research papers
- **🔄 Fallback Support**: Works even when no documents are available
- **📖 Source Citations**: Automatic reference tracking for credibility
- **💬 Natural Flow**: Maintains conversational tone while adding scientific depth

### Example Output Format

```
[Vanilla LLM base response enhanced with RAG details]

Summary:
[concise summary]
```

The system now uses the vanilla LLM response as the foundation and enhances it with specific research details from RAG, maintaining the conversational tone while adding scientific accuracy. The responses are intelligently merged into one cohesive answer without separate sections or labels.

### Testing the Hybrid Approach

Run the test script to see the hybrid approach in action:

```bash
python test_hybrid_approach.py
```

## Usage

Run the API server:

```bash
python run.py
```

The API will be available at `http://localhost:8000` (or your configured host/port).

### Vanilla GPT Comparison Endpoint

Use this endpoint when you want to compare PaperQA-enhanced answers with a plain GPT response.

- **URL**: `POST /query/vanilla`
- **Payload (JSON only)**:

```bash
curl -X POST http://localhost:8000/query/vanilla \
  -H "Content-Type: application/json" \
  -d '{
        "text": "Apa manfaat compound exercise buat muscle growth?"
      }'
```

- **Response fields**:
  - `answer`: GPT output in Bahasa Indonesia (no RAG context)
  - `model`: The model specified via `VANILLA_MODEL_NAME`
  - `usage`: Token usage from the OpenAI Responses API
  - `query`: Echo of the submitted question
  - `status`: `"success"` when generation completes
  - `preferences`: Preferences derived from the authenticated user profile (if a JWT is supplied)

Example call with auth:

```bash
curl -X POST http://localhost:8000/query/vanilla \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token-optional>" \
  -d '{"text": "Apa manfaat compound exercise buat muscle growth?"}'
```

## Evaluation with RAGAS

Run end-to-end evaluation of the PaperQA-based RAG using the latest RAGAS.

1. Ensure dependencies are installed:

```bash
pip install -r requirements.txt
```

2. Prepare dataset at `data/evaluation/dataset.json` as a JSON array of objects:

```json
[{ "question": "...", "expected_answer": "..." }]
```

3. Run the evaluator:

```bash
python -m rag.evaluation.ragas.run_eval --dataset data/evaluation/dataset.json --max-samples 50
```

Optional flags:

- `--model`: judge model (default `gpt-4o-mini`)
- `--save-dir`: output root dir (default `data/evaluation/results`)
- `--docs-dir`: documents dir for RAG (default `./data/sources/processed`)
- `--preferences-text`: inline preference block that mirrors authenticated users
- `--preferences-file`: path to a JSON or plaintext block (see `config/user_preferences_dummy.json`)
- `--use-default-preferences`: apply the bundled dummy profile without editing files

Outputs:

- `data/evaluation/results/<timestamp>/per_sample.csv`
- `data/evaluation/results/<timestamp>/aggregate.json` with `ragas_version`, `judge_model`, and metric aggregates

### Populating datasets with (or without) preferences

Use `populate_dataset.py` to refresh `data/evaluation/dataset.json` and decide whether personalization should be active:

```bash
# Baseline run without user preferences
python populate_dataset.py

# Run with inline preferences
python populate_dataset.py --preferences-text "- Goal: muscle_gain\n- Equipment: resistance bands"

# Run with the bundled dummy profile (also usable for evaluation)
python populate_dataset.py --use-default-preferences
```

You can reuse the same flags with the evaluation script:

```bash
python -m rag.evaluation.ragas.run_eval \
  --dataset data/evaluation/dataset.json \
  --use-default-preferences
```

Both scripts embed the effective preference block in their outputs, making it easy to compare personalized vs. non-personalized runs.

> ℹ️ Whenever preferences are enabled, the generated files are suffixed with `-preferenced`
> (for example `dataset-preferenced.json`, `evaluation_dataset-preferenced.json`) so you can
> keep baseline and personalized artifacts side-by-side.

## License

[Add your license information here]

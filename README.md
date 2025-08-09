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

## Project Structure

- `api/`: FastAPI application code
- `data/`: Data storage
  - `sources/`: Source documents
    - `raw_data/`: Original PDF files
    - `processed_data/`: Processed text files
    - `metadata/`: Metadata about sources
- `llm/`: LLM integration code
- `rag/`: RAG implementation code

## Usage

Run the API server:

```bash
python run.py
```

The API will be available at `http://localhost:8000` (or your configured host/port).

## License

[Add your license information here]

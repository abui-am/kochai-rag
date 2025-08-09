You are building a local Python API for an AI-based Gym Personal Trainer chatbot using:

- ✅ A fine-tuned GPT-4o accessed via OpenAI Playground's API
- ✅ Retrieval-Augmented Generation (RAG) using the `paper-qa` Python package
- ✅ LangChain to orchestrate RAG and GPT-4o prompt handling
- ✅ FastAPI to expose a `/chat` endpoint
- 🚫 No frontend, database, or long-term memory — stateless interaction only

---

📁 Folder Structure:

project-root/
├── api/
│ └── main.py # FastAPI app, handles the /chat endpoint
├── rag/
│ └── paperqa_chain.py # PaperQA loader + LangChain Tool
├── llm/
│ └── gpt_chain.py # LangChain LLM wrapper using GPT-4o
├── data/
│ └── sources/ # Fitness-related PDFs or TXT documents
├── .env # Contains your OpenAI API key
├── requirements.txt # FastAPI, LangChain, PaperQA, etc.
└── README.md

---

🔐 .env File:

OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

---

📦 requirements.txt:

fastapi
uvicorn
openai
langchain
python-dotenv
paper-qa

---

🧠 System Flow:

1. On server startup, load all PDFs from `./data/sources/` using PaperQA (`Docs()`).
2. Wrap `Docs().query()` inside a LangChain `Tool` called `paperqa_tool`.
3. When a POST request is sent to `/chat`, the system:
   - Uses `paperqa_tool` to get an answer + sources from the documents
   - Passes the result as context to GPT-4o using `ChatOpenAI` from LangChain
   - Constructs a final answer with citations using a custom prompt template
4. The server returns:
   - Final GPT-4o response
   - Raw PaperQA context
   - List of source filenames

---

📤 Sample Input:

POST /chat

```json
{
  "message": "Apa manfaat latihan compound untuk pemula?"
}

📥 Sample Output:

{
  "response": "Latihan compound seperti squat dan deadlift melibatkan banyak kelompok otot secara bersamaan...",
  "source_context": "Menurut jurnal di PubMed dan ArXiv, latihan compound meningkatkan efisiensi dan kekuatan otot lebih cepat dibanding isolasi.",
  "sources": ["strength_training_basics.pdf", "pubmed:123456"]
}
📌 Implementation Constraints:


Chatbot responses must be grounded in context from RAG

No memory or history retained between requests

Model used: "gpt-4o" via OpenAI Chat API

✅ Development Tasks:

rag/paperqa_chain.py:

Use Docs() from PaperQA to load all documents

Expose a LangChain Tool named paperqa_tool that wraps .query()

llm/gpt_chain.py:

Create a LangChain ChatOpenAI chain

Use a prompt template like:

Context: {context}
Question: {question}
Based on the context above, generate a helpful fitness answer with citation if applicable.
api/main.py:

Build a FastAPI app

On /chat, take user input → call paperqa_tool → run GPT chain → return answer, context, sources

🧪 Future Add-ons (Optional):

Add test cases using pytest

Build evaluation module using ROUGE/BLEU/BERTScore


```

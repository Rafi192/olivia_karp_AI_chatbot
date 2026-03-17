# olivia_karp_AI_chatbot

![Python](https://img.shields.io/badge/-Python-blue?logo=python&logoColor=white)

##  Description

A production-ready Retrieval-Augmented Generation (RAG) chatbot built with FastAPI, FAISS, and Groq LLM. The system retrieves relevant information from multiple MongoDB collections and generates context-aware responses with multi-turn conversation memory.


##  Features

-  Testing


##  Tech Stack
| Component | Technology |
|---|---|
| API Framework | FastAPI |
| Vector Database | FAISS |
| Embedding Model | BAAI/bge-base-en-v1.5 |
| Reranker | cross-encoder/ms-marco-MiniLM-L-6-v2 |
| LLM | Groq (llama-3.1-8b-instant) |
| Database | MongoDB |
| Chat History | MongoDB (chatbot_db) |
| Prompt Building | LangChain Core |

## Prerequisites

- Python 3.10+
- MongoDB (local or Atlas)
- Groq API key — free at [console.groq.com](https://console.groq.com)
- HuggingFace token — free at [huggingface.co](https://huggingface.co)

---
##  Key Dependencies

```
langchain: latest
langchain-community: latest
langchain-core: latest
langchain-openai         
transformers: latest
sentence-transformers: latest
accelerate: latest
datasets: latest
sentencepiece: latest
huggingface-hub: latest
torch: latest
faiss-cpu                 # CPU version of FAISS: latest
openai                    # optional – only if you still want OpenAI embeddings or fallback LLMs: latest
python-dotenv: latest
fastapi: latest
```

##  Project Structure

```
.
├── chat
│   └── chat_history.py
├── config.py
├── data
│   └── vector_store
│       ├── applyjobs_documents.pkl
│       ├── applyjobs_index.bin
│       ├── blogs_documents.pkl
│       ├── blogs_index.bin
│       ├── courseideas_documents.pkl
│       ├── courseideas_index.bin
│       ├── jobs_documents.pkl
│       ├── jobs_index.bin
│       ├── joinmentorcoaches_documents.pkl
│       ├── joinmentorcoaches_index.bin
│       ├── media_documents.pkl
│       ├── media_index.bin
│       ├── reviews_documents.pkl
│       └── reviews_index.bin
├── ingestion
│   ├── chunker.py
│   ├── embedder.py
│   ├── indexer.py
│   ├── ingest.py
│   ├── load_data.py
│   └── schema.py
├── llm
│   ├── augmented_prompt.py
│   ├── generator.py
│   └── llm_client.py
├── main.py
├── requirements.txt
├── reranker
│   └── reranker.py
├── retriever
│   ├── retriever.py
│   └── router.py
└── tests
    ├── test_db.py
    └── test_rag.py
```

##  Development Setup

**1. Clone the repository**
```bash
git clone https://github.com/your-username/olivia_karp_AI_chatbot.git
cd olivia_karp_AI_chatbot
```

**2. Create and activate virtual environment**
```bash
python -m venv olivia_karp
# Windows
olivia_karp\Scripts\activate
# macOS / Linux
source olivia_karp/bin/activate
```

**3. Install dependencies**
```bash
pip install -r requirements.txt
```

**4. Set up environment variables**

Create a `.env` file in the project root:
```env
# MongoDB
MONGODB_URI=mongodb+srv://your_connection_string
MONGODB_DATABASE=your_main_database_name

# Chatbot database (separate from main app)
CHATBOT_DB=chatbot_db
CHATBOT_HISTORY_COLLECTION=history

# API Keys
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxx
HF_TOKEN=hf_xxxxxxxxxxxxxxxxxxxx
```

---

## Running the System

### Step 1 — Run Ingestion Pipeline

This loads documents from MongoDB, chunks them, embeds them, and builds FAISS indexes. Run this once, and re-run whenever your MongoDB data changes.
```bash
python ingestion/ingest.py
```

Expected output:
```
============================================================
RAG INGESTION PIPELINE
============================================================
[1] Connecting to MongoDB and loading documents...
    Found collections: jobs, applyjobs, blogs, courseideas, ...
[2] Chunking documents...
[3] Loading embedding model...
[4] Building FAISS indexes (one per collection)...
[5] Saving indexes to disk...
============================================================
INGESTION COMPLETE
============================================================
```

### Step 2 — Run Tests (Optional)

Verify the full pipeline works before starting the API:
```bash
python tests/test_rag.py
```

This tests retrieval, reranking, generation, and chat history end-to-end.

### Step 3 — Start the API Server
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000

```

Server runs at `http://127.0.0.1:8000`

API documentation available at `http://127.0.0.1:8000/docs`

---

## API Endpoints

### POST `/api/chat/`
Send a message with user ID and get a response.

**Form fields:**
| Field | Type | Required |
|---|---|---|
| user_id | string | yes |
| query | string | yes |


**Response:**
```json
{
  "status": true,
  "statuscode": 200,
  "text": {
    "user_id": "user123",
    "query": "Show me available jobs",
    "answer": "Here are the available jobs..."
  }
}
```


---

### GET `/api/chat/history/`
Get conversation history for a user.

**Query parameter:** `user_id`



**Example:**
```bash
curl "http://127.0.0.1:8000/api/chat/history/?user_id=user123"
```

**Response:**
```json
{
  "status": true,
  "statuscode": 200,
  "text": {
    "user_id": "user123",
    "history": [
      { "role": "user", "content": "Show me available jobs" },
      { "role": "assistant", "content": "Here are the available jobs..." }
    ]
  }
}
```

---

### DELETE `/api/chat/clear/`
Clear conversation history for a user.

**Form field:** `user_id`

**Example:**
```bash
curl -X DELETE http://127.0.0.1:8000/api/chat/clear/ \
  -F "user_id=user123"
```

---

### GET `/api/health/`
Check if the server is running.
```bash
curl http://127.0.0.1:8000/api/health/
```

---

## Supported MongoDB Collections

| Collection | Description |
|---|---|
| `jobs` | Job listings, requirements, company info |
| `applyjobs` | Job applications, cover letters, status |
| `blogs` | Blog posts, articles, summaries |
| `courseideas` | Course suggestions, skill levels, topics |
| `joinmentorcoaches` | Mentor and coach profiles |
| `reviews` | Reviews and ratings |
| `media` | Media files, PDFs, videos, images |

---

## How It Works

**Data Ingestion (run once)**
1. Loads documents from each MongoDB collection
2. Formats documents using per-collection templates
3. Splits documents into chunks (size: 200, overlap: 20)
4. Embeds chunks using `BAAI/bge-base-en-v1.5`
5. Builds one FAISS index per collection
6. Saves indexes to `data/vector_store/`

**Query Pipeline (per request)**
1. Detects casual queries — skips retrieval for greetings
2. Routes query to relevant collection using Groq LLM
3. Embeds query and searches the routed FAISS index
4. Reranks top-10 results using cross-encoder, keeps top-5
5. Builds augmented prompt with context + chat history
6. Generates response via Groq `llama-3.1-8b-instant`
7. Saves both turns to MongoDB chat history

---

## Re-indexing After Data Changes

Whenever you add or update data in MongoDB, re-run the ingestion:
```bash
python ingestion/ingest.py
```

This rebuilds all FAISS indexes with the latest data.

---

## Requirements
```
fastapi
uvicorn
pymongo
python-dotenv
faiss-cpu
sentence-transformers
langchain-core
groq
huggingface-hub
beautifulsoup4
numpy
python-multipart
```


## Environment Variables Reference

| Variable | Description |
|---|---|
| `MONGODB_URI` | MongoDB connection string |
| `MONGODB_DATABASE` | Main application database name |
| `CHATBOT_DB` | Chatbot database name (default: `chatbot_db`) |
| `CHATBOT_HISTORY_COLLECTION` | History collection name (default: `history`) |
| `GROQ_API_KEY` | Groq API key for LLM generation |
| `HF_TOKEN` | HuggingFace token for model downloads |

---

## License

MIT License
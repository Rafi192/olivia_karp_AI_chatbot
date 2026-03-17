# olivia_karp_AI_chatbot

![Python](https://img.shields.io/badge/-Python-blue?logo=python&logoColor=white)

##  Description

A sophisticated, Python-driven AI chatbot designed specifically for the Olivia Karp website to enhance user interaction and streamline client communication. Leveraging advanced natural language processing capabilities, this intelligent assistant provides automated, real-time support for visitors. The project emphasizes reliability through comprehensive testing protocols, ensuring consistent and accurate responses to meet business needs effectively.

##  Features

-  Testing


##  Tech Stack

-  Python


##  Key Dependencies

```
langchain: latest
langchain-community: latest
langchain-core: latest
langchain-openai          # keep if you still want to call OpenAI as a fallback: latest
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

### Python Setup
1. Install Python (v3.11+ recommended)
2. Create a virtual environment: `python -m venv venv`
3. Activate the environment:
   - Windows: `venv\Scripts\activate`
   - Unix/MacOS: `source venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`

### Step 2- 
 - Run Data Ingestion (One-Time Setup)
This creates the FAISS vector index from our MongoDB collections:

```
cd ingestion
python ingest.py

```

## step 3

run the Fast API app from the root folder

uvicorn main:app --reload
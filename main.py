# main.py
import os
import sys
import uuid
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from fastapi import FastAPI, Form
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
import logging

from chat.chat_history import ChatHistory
from retriever.retriever import Retriever
from reranker.reranker import Reranker
from llm.generator import generate_response

from ingestion.schema import is_casual_query

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI()

# initialise once at startup — shared across all requests
chat_history = ChatHistory()
retriever    = Retriever()
reranker     = Reranker()


@app.post("/api/chat/")
def chat(
    user_id: str = Form(),
    query:   str = Form()
):
    try:
        if is_casual_query(query):
            answer = generate_response(
                query=query,
                chunks=[],          # empty — no context needed
                chat_history=[]
            )
            chat_history.add_message(user_id, "user",      query)
            chat_history.add_message(user_id, "assistant", answer)

            return JSONResponse(
                status_code=200,
                content={
                    "status":     True,
                    "statuscode": 200,
                    "text": {
                        "user_id": user_id,
                        "query":   query,
                        "answer":  answer
                    }
                }
            )
        
        #normal RAG flow for real queries
        # 1  get the user's previous history
        history = chat_history.get_history(user_id)

        # 2 — retrieve + rerank
        chunks   = retriever.retrieve(query, top_k=10)
        reranked = reranker.rerank(query, chunks, top_k=5)

        # 3 — generate
        answer = generate_response(
            query=query,
            chunks=reranked,
            chat_history=history
        )

        # 4 — save both turns
        chat_history.add_message(user_id, "user",      query)
        chat_history.add_message(user_id, "assistant", answer)

        return JSONResponse(
            status_code=200,
            content={
                "status":     True,
                "statuscode": 200,
                "text": {
                    "user_id": user_id,
                    "query":   query,
                    "answer":  answer
                }
            }
        )

    except Exception as ex:
        logger.exception("Chat endpoint failed")
        return JSONResponse(
            status_code=500,
            content={
                "status":     False,
                "statuscode": 500,
                "text":       str(ex)
            }
        )


@app.delete("/api/chat/clear/")
def clear_chat(user_id: str = Form()):
    try:
        chat_history.clear_session(user_id)
        return JSONResponse(
            status_code=200,
            content={
                "status":     True,
                "statuscode": 200,
                "text":       f"History cleared for user {user_id}"
            }
        )

    except Exception as ex:
        logger.exception("Clear chat failed")
        return JSONResponse(
            status_code=500,
            content={
                "status":     False,
                "statuscode": 500,
                "text":       str(ex)
            }
        )


@app.get("/api/chat/history/")
def get_history(user_id: str = Form()):
    try:
        history = chat_history.get_history(user_id)

        if not history:
            return JSONResponse(
                status_code=404,
                content={
                    "status":     False,
                    "statuscode": 404,
                    "text":       "No history found for this user"
                }
            )

        return JSONResponse(
            status_code=200,
            content={
                "status":     True,
                "statuscode": 200,
                "text": {
                    "user_id": user_id,
                    "history": history
                }
            }
        )

    except Exception as ex:
        logger.exception("Get history failed")
        return JSONResponse(
            status_code=500,
            content={
                "status":     False,
                "statuscode": 500,
                "text":       str(ex)
            }
        )


@app.get("/api/health/")
def health_check():
    return JSONResponse(
        status_code=200,
        content={
            "status":     True,
            "statuscode": 200,
            "text":       "RAG chatbot is running"
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
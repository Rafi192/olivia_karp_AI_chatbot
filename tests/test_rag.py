# tests/test_rag.py
import sys
import os
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

from retriever.retriever import Retriever
from reranker.reranker   import Reranker
from llm.generator       import generate_response
from chat.chat_history   import ChatHistory

import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


TEST_QUERIES = [
    "can you give me the portfolio or linkedin url of an applied jobs?",
    "share the thumbnai and file url video uploaded by ayesha Rahman",
    "share the thumbnai and file url video on wildlife documentary of sundarbans",
    "Are there any remote jobs?",        # follow-up — tests chat history
    "What kind of blogs are available?",
    "Show me course ideas",
    "What is the status of job applications?"
    

]

TEST_USER_ID = "test_user_002"


def separator(title: str):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def test_retriever(retriever: Retriever, query: str):
    separator(f"RETRIEVER — '{query}'")
    chunks = retriever.retrieve(query, top_k=10)

    if not chunks:
        print("  No chunks retrieved")
        return chunks

    print(f"  Retrieved {len(chunks)} chunks")
    for i, chunk in enumerate(chunks, 1):
        collection = chunk.get("metadata", {}).get("collection", "unknown")
        score      = chunk.get("similarity_score", 0)
        preview    = chunk.get("text", "")[:80].replace("\n", " ")
        print(f"  [{i}] {collection} | score: {score:.4f} | {preview}...")

    return chunks


def test_reranker(reranker: Reranker, query: str, chunks: list):
    separator(f"RERANKER — '{query}'")

    if not chunks:
        print("  No chunks to rerank")
        return chunks

    reranked = reranker.rerank(query, chunks, top_k=5)

    print(f"  Reranked → kept top {len(reranked)}")
    for i, chunk in enumerate(reranked, 1):
        collection   = chunk.get("metadata", {}).get("collection", "unknown")
        rerank_score = chunk.get("rerank_score", 0)
        sim_score    = chunk.get("similarity_score", 0)
        preview      = chunk.get("text", "")[:80].replace("\n", " ")
        print(f"  [{i}] {collection} | rerank: {rerank_score:.4f} | sim: {sim_score:.4f} | {preview}...")

    return reranked


def test_generator(query: str, chunks: list, history: list):
    separator(f"GENERATOR — '{query}'")

    if not chunks:
        print("  No chunks — skipping generation")
        return None

    print(f"  History turns: {len(history)}")
    answer = generate_response(
        query=query,
        chunks=chunks,
        chat_history=history
    )

    print(f"\n  Answer:\n  {answer}")
    return answer


def test_chat_history(chat_history: ChatHistory):
    separator("CHAT HISTORY")

    # add test messages
    chat_history.add_message(TEST_USER_ID, "user",      "hello")
    chat_history.add_message(TEST_USER_ID, "assistant", "hi, how can I help?")

    history = chat_history.get_history(TEST_USER_ID)
    print(f"  Stored and retrieved {len(history)} messages")
    for msg in history:
        print(f"  [{msg['role']}]: {msg['content']}")

    # clear after test
    chat_history.clear_session(TEST_USER_ID)
    print(f"  Session cleared")


def run_full_pipeline():
    separator("INITIALISING COMPONENTS")

    print("  Loading retriever...")
    retriever = Retriever()

    print("  Loading reranker...")
    reranker = Reranker()

    print("  Loading chat history...")
    chat_history = ChatHistory()

    print("  All components loaded")

    # ── test chat history ────────────────────────────────────────
    test_chat_history(chat_history)

    # ── test full pipeline with multi-turn ───────────────────────
    separator("FULL PIPELINE — MULTI-TURN TEST")

    history = []

    for query in TEST_QUERIES:
        print(f"\n  User: {query}")

        # retrieve
        chunks   = test_retriever(retriever, query)

        # rerank
        reranked = test_reranker(reranker, query, chunks)

        # generate
        answer   = test_generator(query, reranked, history)

        if answer:
            # update history for next turn
            history.append({"role": "user",      "content": query})
            history.append({"role": "assistant",  "content": answer})

            # keep last 6 messages only
            history = history[-6:]

        print(f"\n  History length so far: {len(history)} messages")

    separator("ALL TESTS COMPLETE")
    print("  Pipeline is working end to end")
    print("  You can now test the FastAPI endpoints")
    print(f"  Run: uvicorn main:app --reload")


if __name__ == "__main__":
    try:
        run_full_pipeline()
    except KeyboardInterrupt:
        print("\n\n  Interrupted.")
    except Exception as e:
        logger.exception(f"Test failed: {e}")
        sys.exit(1)
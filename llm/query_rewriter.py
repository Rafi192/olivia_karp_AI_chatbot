# retriever/query_rewriter.py
import logging
from datetime import datetime
from ingestion.schema import is_casual_query
from llm.llm_client import get_client, get_model_name, active_model, LLMProvider

logger = logging.getLogger(__name__)



def rewrite_query(query: str, chat_history: list) -> str:
    """
    Rewrite the user query into a standalone search query.

    Skips rewriting entirely when:
    - There is no chat history (nothing to resolve)
    - The query is casual (no retrieval will happen anyway)

    This saves one LLM API call on every first message and every greeting,
    which is the majority of conversation-opening turns.
    """

    # ── Skip 1: no history → nothing to resolve, original query is best ──────
    if not chat_history:
        logger.info(f"No history — skipping rewrite, using original: '{query}'")
        return query

    # ── Skip 2: casual query → retrieval won't run anyway ────────────────────
    if is_casual_query(query):
        logger.info(f"Casual query — skipping rewrite: '{query}'")
        return query

    # ── Rewrite only when there is real history to resolve ───────────────────
    today = datetime.utcnow().strftime("%B %Y")   # e.g. "April 2026"

    history_text = "\n".join(
        f"{m['role'].capitalize()}: {m['content']}"
        for m in chat_history[-6:]
    )

    prompt = f"""You are a search query rewriting system for a RAG chatbot about a job platform.

Today's date: {today}

Your job:
- Rewrite the user's question into a clear, standalone search query (max 20 words).
- Resolve pronouns and vague references using the chat history.
- PRESERVE personal details the user mentions (job role, interests, skill level, preferences).
- For time-sensitive queries ("now", "available", "current"), include the current date/year.
- Do NOT answer the question.
- Do NOT add information that is not in the query or history.

Chat History:
{history_text}

User Query: {query}

Rewritten query (max 20 words, return ONLY the query):"""

    try:
        client = get_client()
        model  = get_model_name()

        # HuggingFace uses a different API shape
        if active_model == LLMProvider.HF:
            response = client.text_generation(
                prompt,
                model=model,
                max_new_tokens=40,
                temperature=0.0,
                stop_sequences=["\n"],
            )
            rewritten = response.strip()
        else:
            # OpenAI and Groq share the same interface
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
                max_tokens=40,
            )
            rewritten = response.choices[0].message.content.strip()

        # Sanity guard — if the model returned something suspiciously long
        # or started answering instead of rewriting, fall back to original
        if not rewritten or len(rewritten.split()) > 25:
            logger.warning(f"Rewriter returned suspicious output — using original query")
            return query

        logger.info(f"Rewritten: '{query}' → '{rewritten}'")
        return rewritten

    except Exception as e:
        logger.error(f"Query rewrite failed: {e} — using original query")
        return query   # always safe to fall back to the original
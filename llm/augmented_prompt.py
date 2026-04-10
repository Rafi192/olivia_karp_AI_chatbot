# llm/augmented_prompt.py
import logging
from typing import List, Dict, Any
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import PromptTemplate
from chat.chat_history import ChatHistory

logger = logging.getLogger(__name__)


def format_retrieved_chunks(chunks: List[Dict[str, Any]]) -> str:
  
    if not chunks:
        return "No relevant information found."

    context_parts = []

    for i, chunk in enumerate(chunks, 1):
        text       = chunk.get("text", "")
        metadata   = chunk.get("metadata", {})
        collection = metadata.get("collection", "unknown")

        # block = f"[Source {i} — {collection}]\n{text}"
        block = f"[Context {i}]\n{text}"

        # Append any URLs stored in metadata
        for url_field in ["companyURL", "portfolioUrl", "linkedinUrl"]:
            val = metadata.get(url_field, "")
            if val:
                block += f"\n{url_field}: {val}"

        context_parts.append(block)

    return "\n\n".join(context_parts)


def format_chat_history(chat_history: List[Dict[str, str]]) -> str:
    """
    Format last 3 exchanges (6 messages) into readable history string.
    """
    if not chat_history:
        return ""

    turns = []
    for turn in chat_history[-6:]:
        role    = turn.get("role", "")
        content = turn.get("content", "")
        if role == "user":
            turns.append(f"User: {content}")
        elif role == "assistant":
            turns.append(f"Assistant: {content}")

    return "\n".join(turns)


def build_augmented_prompt(
    query: str,
    chunks: List[Dict[str, Any]],
    chat_history: List[Dict[str, str]] = None
) -> str:
     # ── casual query — no context needed ────────────────────────
    if not chunks:
        sys_message = SystemMessage(
            content=(
                "You are a helpful AI assistant for a job platform. "
                "Respond naturally and friendly to the user's message. "
                "Keep it brief and helpful."
            )
        )
        hum_message = HumanMessage(content=query)
        template = PromptTemplate(
            template="{sys_message}\n\n{hum_message}",
            input_variables=["sys_message", "hum_message"]
        )
        prompt = template.invoke({
            "sys_message": sys_message.content,
            "hum_message": hum_message.content,
        })
        return prompt.text
    
     # ── normal RAG prompt below ──────────────────────────────────
   
    context      = format_retrieved_chunks(chunks)
    history_text = format_chat_history(chat_history or [])

    sys_message = SystemMessage(
        content=(
            "You are a helpful AI assistant for a job platform.\n"
            "Answer the user's question using ONLY the context provided below.\n"
            "Rules:\n"
            "- Answer clearly and concisely using only the context.\n"
            "- If the context contains URLs or links, include them in your answer.\n"
            "- If the answer is NOT in the context, say: "
            "'I don't have enough information to answer that.'\n"
            "- Do NOT hallucinate or add any information not present in the context.\n"
            "- Keep answers focused and relevant to the question.\n"
            "- Do NOT reference 'Source', 'Context', or collection names in your answer.\n"
            "- Synthesize the information naturally as if you know it.\n"
        )
    )

    hum_content = ""

    if history_text:
        hum_content += f"Conversation History:\n{history_text}\n\n"

    hum_content += (
        f"Context:\n{context}\n\n"
        f"User Question: {query}"
    )

    hum_message = HumanMessage(content=hum_content)

    template = PromptTemplate(
        template="{sys_message}\n\n{hum_message}",
        input_variables=["sys_message", "hum_message"]
    )

    prompt = template.invoke({
        "sys_message": sys_message.content,
        "hum_message": hum_message.content,
    })

    logger.info(f"Built augmented prompt ({len(prompt.text)} chars)")
    return prompt.text
from llm.llm_client import get_client, get_model_name, active_model, LLMProvider

def rewrite_query(query: str, chat_history: list) -> str:
   

    history_text = ""
    if chat_history:
        history_text = "\n".join(
            [f"{m['role']}: {m['content']}" for m in chat_history[-6:]]
        )

    prompt = f"""
You are a query rewriting system for a RAG chatbot.

Your job:
- Convert the user question into a clear standalone search query
- PRESERVE any personal details the user mentions (profession, interests, level)
- Use chat history to resolve pronouns and references
- DO NOT answer the question
- DO NOT over-compress — preserve nuance

Chat History:
{history_text}

User Query: {query}

Return ONLY the rewritten query. Keep it under 15 words.
"""

    client = get_client()
    model = get_model_name()

    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )

    return response.choices[0].message.content.strip()
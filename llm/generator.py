# llm/generator.py
import logging
from typing import List, Dict, Any
from llm.llm_client import get_client, get_model_name, active_model, LLMProvider
from llm.augmented_prompt import build_augmented_prompt

logger = logging.getLogger(__name__)


def generate_response(
    query: str,
    chunks: List[Dict[str, Any]],
    chat_history: List[Dict[str, str]] = None,
    max_new_tokens: int = 512
) -> str:
   
    try:
        # Step 1 — build augmented prompt
        prompt = build_augmented_prompt(
            query=query,
            chunks=chunks,
            chat_history=chat_history or []
        )

        logger.info(f"Prompt length: {len(prompt)} chars")

        # Step 2 — call LLM
        client     = get_client()
        model_name = get_model_name()

        if active_model == LLMProvider.GROQ:
            response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_new_tokens,
                temperature=0.3,
            )
            result = response.choices[0].message.content.strip()

        else:  # HuggingFace
            response = client.chat_completion(
             messages=[{"role": "user", "content": prompt}],
            model=model_name,
            max_tokens=512,
            temperature=0.3,
)
            result = response.choices[0].message.content.strip()

        logger.info(f"Generated {len(result)} chars via {active_model}")
        return result

    except Exception as e:
        logger.error(f"Generation failed: {e}")
        return "I'm sorry, I was unable to generate a response. Please try again."
# retriever/router.py
import logging
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import PromptTemplate
from llm.llm_client import get_client, get_model_name, active_model, LLMProvider

logger = logging.getLogger(__name__)

COLLECTION_DESCRIPTIONS = {
    "jobs":               "Job listings, company info, requirements, skills, location, job type",
    "applyjobs":          "Job applications, cover letters, applicant status, portfolio links",
    "blogs":              "Blog posts, articles, environment, technology, summaries and full content",
    "courseideas":        "Course ideas, skill levels, key topics, learning content suggestions",
    "joinmentorcoaches":  "Mentor and coach profiles, expertise, availability, experience",
    "reviews":            "Reviews and ratings for events, courses, and services",
    "media":              "Media files, PDFs, webinar slides, videos and descriptions",
}
COLLECTION_NAMES = list(COLLECTION_DESCRIPTIONS.keys())


def build_router_prompt(query: str) -> str:
    sys_message = SystemMessage(
        content=(
            "You are a routing assistant for a RAG system.\n"
            "Your job is to read the user query and return ONLY the single most relevant "
            "collection name from the list provided.\n"
            "Rules:\n"
            "Return 1-3 collection names separated by commas, most relevant first.\n"
            "Return only relevant names from the list. \n"
            "- No explanation, no punctuation, no extra words.\n"
            
        )
    )

    collection_list = "\n".join(
        f"- {name}: {desc}"
        for name, desc in COLLECTION_DESCRIPTIONS.items()
    )

    hum_message = HumanMessage(
        content=(
            f"Available collections:\n{collection_list}\n\n"
            f"User query: {query}\n\n"
            f"Collection name:"
        )
    )

    template = PromptTemplate(
        template="{sys_message}\n\n{hum_message}",
        input_variables=["sys_message", "hum_message"]
    )

    return template.invoke({
        "sys_message": sys_message.content,
        "hum_message": hum_message.content,
    }).text


def route_query(query: str) -> list[str]:
    try:
        client     = get_client()
        model_name = get_model_name()
        prompt     = build_router_prompt(query)

        if active_model == LLMProvider.GROQ:
            response = client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=10,
                temperature=0.0,   # fully deterministic for routing
            )
            collection = response.choices[0].message.content.strip().lower()

        else:  # HuggingFace
            response = client.text_generation(
                prompt,
                model=model_name,
                max_new_tokens=10,
                temperature=0.1,
                stop_sequences=["\n", ".", ",", " "],
            )
            collection = response.strip().lower()

        logger.info(f"Router raw response: '{collection}'")

        if collection in COLLECTION_NAMES:
            logger.info(f"Routed '{query[:60]}' → '{collection}'")
            return [collection]
        else:
            logger.warning(f"Unknown collection '{collection}', searching all")
            return COLLECTION_NAMES

    except Exception as e:
        logger.error(f"Router failed: {e}, falling back to all collections")
        return COLLECTION_NAMES
import os
import logging
from enum import Enum

logger = logging.getLevelName(__name__)

class LLMProvider(str, Enum):
    HF = "huggingface"
    GROQ = "groq"


# HF_MODEL   = "meta-llama/Llama-3.2-3B-Instruct"
HF_MODEL = "mistralai/Mistral-7B-Instruct-v0.3"
GROQ_MODEL = "llama-3.1-8b-instant"

active_model = LLMProvider.GROQ

def get_hf_client():
    from huggingface_hub import InferenceClient
    api_key = os.getenv("HF_API_KEY")
    if not api_key:
        raise ValueError("HF_API_KEY not found in .env")
    return InferenceClient(token=api_key)

def get_groq_client():
    from groq import Groq
    api_key = os.getenv("groq_api_key")
    if not api_key:
        raise ValueError("GROQ_API_KEY not found in .env")
    return Groq(api_key=api_key)


def get_client():
    if active_model == LLMProvider.GROQ:
        return get_groq_client()
    return get_hf_client()


def get_model_name():
    if active_model == LLMProvider.GROQ:
        return GROQ_MODEL
    
    return HF_MODEL


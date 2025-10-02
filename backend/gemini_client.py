# backend/gemini_client.py
from dotenv import load_dotenv
import os
import google.generativeai as genai

# Load environment variables from .env file
load_dotenv()

GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-pro")
EMBED_MODEL  = os.getenv("EMBED_MODEL", "text-embedding-004")

def configure():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not set")
    genai.configure(api_key=api_key)

def model():
    configure()
    print("Using model:", GEMINI_MODEL)  # Debugging statement
    return genai.GenerativeModel(GEMINI_MODEL)

def embed_texts(texts):
    configure()
    try:
        res = genai.embed_content(model=EMBED_MODEL, content=texts)
        print(f"Embedding response: {res}")
        return res['embedding']
    except Exception as e:
        print(f"Error during embedding generation: {e}")
        raise RuntimeError(f"Embedding generation failed: {e}")

def list_available_models():
    configure()
    try:
        models = genai.list_models()
        models_list = list(models)  # Convert the generator to a list
        print(f"Available models: {models_list}")
        return models_list
    except Exception as e:
        print(f"Error fetching model list: {e}")
        raise RuntimeError(f"Failed to fetch model list: {e}")

from backend.gemini_client import list_available_models
list_available_models()

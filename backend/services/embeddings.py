"""The embedding model, chosen once per process.

Vectors from different models live in different spaces, and here in different
sizes too (Gemini's are 3072-d, the local model's 384-d), so one index can
never hold both. The model is picked at startup and never switched at runtime;
VectorStoreService keeps a separate Chroma collection per model.
"""
import google.generativeai as genai
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from typing import Any, List, Tuple
import os

LOCAL_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
DEFAULT_GEMINI_MODEL = "models/gemini-embedding-001"


class GeminiEmbeddings(GoogleGenerativeAIEmbeddings):
    # langchain-google-genai 0.0.6's _embed swaps the task type it is given for
    # "retrieval_document", so questions were embedded as if they were
    # documents. Queries ask for "retrieval_query" directly.
    def embed_query(self, text: str) -> List[float]:
        return genai.embed_content(model=self.model, content=text, task_type="retrieval_query")["embedding"]


def load_embeddings() -> Tuple[Any, str]:
    """Return (embeddings, model name) as configured by EMBEDDING_MODEL.

    EMBEDDING_MODEL=local runs offline on a sentence-transformers model; any
    other value names a Gemini embedding model. Unset: Gemini when
    GEMINI_API_KEY is set, local otherwise.
    """
    model = os.getenv("EMBEDDING_MODEL") or (DEFAULT_GEMINI_MODEL if os.getenv("GEMINI_API_KEY") else "local")
    if model == "local":
        # Imported here: sentence-transformers pulls in torch, which a
        # Gemini-only process never needs to load.
        from langchain_community.embeddings import HuggingFaceEmbeddings

        embeddings = HuggingFaceEmbeddings(
            model_name=LOCAL_MODEL,
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )
        return embeddings, LOCAL_MODEL
    return GeminiEmbeddings(  # type: ignore[call-arg]
        model=model, google_api_key=os.getenv("GEMINI_API_KEY")
    ), model

from langchain_google_genai import GoogleGenerativeAIEmbeddings
from typing import List, Optional, Any
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FallbackEmbeddings:
    """
    Embedding service that tries Gemini first, falls back to local HuggingFace embeddings.
    Lazy loads HuggingFace only when needed to avoid startup issues.
    """
    def __init__(self) -> None:
        self.use_fallback: bool = False
        self.fallback_embeddings: Optional[Any] = None  # Lazy load
        self.primary_embeddings: Optional[GoogleGenerativeAIEmbeddings] = None
        # Primary: Gemini embeddings — model can be overridden via GEMINI_MODEL.
        # Construction makes no API call: it only fails when no key is set. A bad
        # model or key shows up on the first embed, which then switches to local.
        self.primary_model = os.getenv("GEMINI_MODEL") or "models/gemini-embedding-001"
        try:
            self.primary_embeddings = GoogleGenerativeAIEmbeddings(  # type: ignore[call-arg]
                model=self.primary_model,
                google_api_key=os.getenv("GEMINI_API_KEY")
            )
        except Exception as e:
            logger.warning(f"⚠️ Gemini embeddings unavailable, using local fallback: {e}")
            self.use_fallback = True

    def _load_fallback(self):
        """Lazy load fallback embeddings only when needed"""
        if self.fallback_embeddings is None:
            try:
                logger.info("📦 Loading fallback embeddings (HuggingFace)...")
                from langchain_community.embeddings import HuggingFaceEmbeddings

                self.fallback_embeddings = HuggingFaceEmbeddings(
                    model_name="sentence-transformers/all-MiniLM-L6-v2",
                    model_kwargs={'device': 'cpu'},
                    encode_kwargs={'normalize_embeddings': True}
                )
                logger.info("✅ Fallback embeddings loaded successfully")
            except Exception as e:
                # Never substitute placeholder vectors: an index built on them
                # fails silently, returning confident nonsense instead of an error.
                raise RuntimeError(
                    "No usable embedding model: Gemini is unavailable and the local "
                    "HuggingFace fallback failed to load."
                ) from e

    @property
    def mode(self) -> str:
        """Which embedding backend is live: 'gemini' or 'local'."""
        return "gemini" if self._primary_live else "local"

    @property
    def _primary_live(self) -> bool:
        return not self.use_fallback and self.primary_embeddings is not None

    @property
    def is_degraded(self) -> bool:
        """True when answers are not backed by the primary embedding model."""
        return self.mode != "gemini"

    def _embed(self, method: str, arg: Any) -> Any:
        if self._primary_live:
            try:
                return getattr(self.primary_embeddings, method)(arg)
            except Exception as e:
                # Quota (429), bad key or bad model: switch to the local model
                # until /api/reset-embeddings.
                logger.warning(f"⚠️ Gemini embeddings failed, switching to fallback: {e}")
                self.use_fallback = True
        self._load_fallback()
        return getattr(self.fallback_embeddings, method)(arg)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return self._embed("embed_documents", texts)

    def embed_query(self, text: str) -> List[float]:
        return self._embed("embed_query", text)

    def reset_to_primary(self):
        """Reset to attempt Gemini embeddings again (call after quota recovery)"""
        self.use_fallback = False
        logger.info("🔄 Reset to primary (Gemini) embeddings")

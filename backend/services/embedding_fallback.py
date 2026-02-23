from langchain_google_genai import GoogleGenerativeAIEmbeddings
from typing import List, Optional, Any
import os
from dotenv import load_dotenv
import logging
from config import settings

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# List of known-good Gemini embedding models
KNOWN_GOOD_MODELS = [
    "models/embedding-001",
    "models/text-embedding-004",
]

# Known problematic models to avoid
PROBLEMATIC_MODELS = [
    "models/gemini-2.0-flash-exp",
    "models/gemini-pro",
]


class FallbackEmbeddings:
    """
    Embedding service that tries Gemini first, falls back to local HuggingFace embeddings.
    Lazy loads HuggingFace only when needed to avoid startup issues.
    Includes model validation to catch NotFound errors early and suggest alternatives.
    """
    def __init__(self) -> None:
        self.gemini_api_key: Optional[str] = os.getenv("GEMINI_API_KEY")
        self.use_fallback: bool = False
        self.fallback_embeddings: Optional[Any] = None  # Lazy load
        self.primary_embeddings: Optional[GoogleGenerativeAIEmbeddings] = None
        
        # Primary: Gemini embeddings — model can be overridden via env or config
        self.primary_model = os.getenv("GEMINI_MODEL") or getattr(settings, "gemini_model", "models/embedding-001")
        
        # Validate model choice
        if self.primary_model in PROBLEMATIC_MODELS:
            logger.warning(f"⚠️ Model '{self.primary_model}' is known to be unavailable for embeddings. Using fallback.")
            self.use_fallback = True
        elif self.primary_model not in KNOWN_GOOD_MODELS and not self.primary_model.startswith("models/"):
            logger.warning(f"⚠️ Model '{self.primary_model}' may not be valid. Known good models: {', '.join(KNOWN_GOOD_MODELS)}")
        
        if not self.use_fallback:
            try:
                logger.info(f"Trying Gemini embeddings model: {self.primary_model}")
                self.primary_embeddings = GoogleGenerativeAIEmbeddings(  # type: ignore
                    model=self.primary_model,
                    google_api_key=self.gemini_api_key
                )
                logger.info("✅ Gemini embeddings initialized")
            except Exception as e:
                error_msg = str(e)
                # Check for NotFound or model availability errors
                if "404" in error_msg or "notfound" in error_msg.lower() or "not found" in error_msg.lower():
                    logger.warning(f"⚠️ Model '{self.primary_model}' not available (404). Available models: {', '.join(KNOWN_GOOD_MODELS)}")
                    logger.info(f"💡 Tip: Set GEMINI_MODEL='{KNOWN_GOOD_MODELS[0]}' to use a known-good model")
                else:
                    logger.warning(f"⚠️ Gemini embeddings failed to initialize (model={self.primary_model}): {e}")
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
                logger.error(f"❌ Failed to load fallback embeddings: {e}")
                # Last resort: return dummy embeddings
                logger.warning("⚠️ Using dummy embeddings as last resort")
                self.fallback_embeddings = DummyEmbeddings()
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed a list of documents"""
        if not self.use_fallback and self.primary_embeddings is not None:
            try:
                logger.info("🔄 Using Gemini embeddings...")
                return self.primary_embeddings.embed_documents(texts)
            except Exception as e:
                error_msg = str(e)
                if "429" in error_msg or "quota" in error_msg.lower():
                    logger.warning("⚠️ Gemini quota exceeded, switching to fallback")
                    self.use_fallback = True
                else:
                    logger.error(f"❌ Gemini embedding error: {e}")
                    self.use_fallback = True
        
        # Use fallback
        logger.info("🔄 Using fallback embeddings...")
        self._load_fallback()
        if self.fallback_embeddings is not None:
            return self.fallback_embeddings.embed_documents(texts)
        return [[0.0] * 384 for _ in texts]  # Fallback if nothing is available

    def reset_to_primary(self):
        """Reset to attempt Gemini embeddings again (call after quota recovery)"""
        self.use_fallback = False
        self.fallback_embeddings = None
        logger.info("🔄 Reset to primary (Gemini) embeddings")

    def embed_query(self, text: str) -> List[float]:
        """Embed a query"""
        if not self.use_fallback and self.primary_embeddings is not None:
            try:
                return self.primary_embeddings.embed_query(text)
            except Exception as e:
                error_msg = str(e)
                if "429" in error_msg or "quota" in error_msg.lower():
                    logger.warning("⚠️ Gemini quota exceeded, switching to fallback")
                    self.use_fallback = True
                else:
                    logger.error(f"❌ Gemini embedding error: {e}")
                    self.use_fallback = True
        
        # Use fallback
        self._load_fallback()
        if self.fallback_embeddings is not None:
            return self.fallback_embeddings.embed_query(text)
        return [0.0] * 384  # Fallback if nothing is available


class DummyEmbeddings:
    """Dummy embeddings as absolute fallback if everything fails"""
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Return dummy embeddings (384 dimensions for compatibility)"""
        import hashlib
        import struct
        
        embeddings = []
        for text in texts:
            # Create deterministic embeddings from text hash
            hash_obj = hashlib.sha256(text.encode())
            hash_bytes = hash_obj.digest()
            
            # Convert to 384 floats (common embedding size)
            embedding = []
            for i in range(0, len(hash_bytes), 4):
                chunk = hash_bytes[i:i+4].ljust(4, b'\0')
                val = struct.unpack('f', chunk)[0] if len(chunk) == 4 else 0.0
                embedding.append(val)
            
            # Pad to 384 dimensions
            while len(embedding) < 384:
                embedding.append(0.0)
            
            embeddings.append(embedding[:384])
        
        return embeddings
    
    def embed_query(self, text: str) -> List[float]:
        """Return dummy embedding for query"""
        return self.embed_documents([text])[0]
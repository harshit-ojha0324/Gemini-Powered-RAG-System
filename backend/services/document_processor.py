import os
import re
import math
from typing import List, Optional, Any

from pypdf import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document

# Split on sentence-ending punctuation followed by whitespace and a capital/quote/digit.
_SENTENCE_BOUNDARY = re.compile(r'(?<=[.!?])\s+(?=[A-Z0-9"\'])')


class SemanticChunker:
    """Embedding-similarity ("semantic") chunker.

    Instead of cutting text at a fixed character count, this splits the text into
    sentences, embeds each sentence, and starts a new chunk wherever the cosine
    distance between two consecutive sentences rises above a percentile threshold
    — i.e. at a topic shift. Chunks therefore follow the document's semantics
    rather than an arbitrary window.

    It degrades gracefully to recursive character splitting when there aren't
    enough sentences to reason about, when embeddings are unavailable, or when the
    embeddings are degenerate (e.g. the dummy SHA-256 fallback carries no signal).
    """

    def __init__(
        self,
        embeddings: Any,
        breakpoint_percentile: int = 90,
        min_chunk_chars: int = 250,
        max_chunk_chars: int = 1500,
        max_sentences: int = 400,
        fallback_splitter: Optional[RecursiveCharacterTextSplitter] = None,
    ):
        self.embeddings = embeddings
        self.breakpoint_percentile = breakpoint_percentile
        self.min_chunk_chars = min_chunk_chars
        self.max_chunk_chars = max_chunk_chars
        self.max_sentences = max_sentences
        self.fallback_splitter = fallback_splitter or RecursiveCharacterTextSplitter(
            chunk_size=1000, chunk_overlap=200, length_function=len,
            separators=["\n\n", "\n", " ", ""],
        )

    # -- public API mirrors LangChain splitters so it's a drop-in replacement --
    def split_documents(self, documents: List[Document]) -> List[Document]:
        chunks: List[Document] = []
        for doc in documents:
            for piece in self.split_text(doc.page_content):
                chunks.append(Document(page_content=piece, metadata=dict(doc.metadata)))
        return chunks

    def split_text(self, text: str) -> List[str]:
        text = (text or "").strip()
        if not text:
            return []
        if len(text) <= self.min_chunk_chars:
            return [text]

        sentences = self._split_sentences(text)
        # Too few sentences to reason about a topic shift, or so many that the
        # per-sentence embedding pass isn't worth it — fall back to char splitting.
        if len(sentences) < 3 or len(sentences) > self.max_sentences:
            return self._fallback(text)

        try:
            vectors = self.embeddings.embed_documents(sentences)
        except Exception:
            return self._fallback(text)

        distances = [
            self._cosine_distance(vectors[i], vectors[i + 1])
            for i in range(len(vectors) - 1)
        ]
        # Constant distances => no semantic signal (dummy embeddings) => fall back.
        if not distances or (max(distances) - min(distances)) < 1e-6:
            return self._fallback(text)

        threshold = self._percentile(distances, self.breakpoint_percentile)

        chunks: List[str] = []
        current = [sentences[0]]
        for i, dist in enumerate(distances):
            nxt = sentences[i + 1]
            current_len = sum(len(s) + 1 for s in current)
            hit_topic_shift = dist >= threshold and current_len >= self.min_chunk_chars
            would_overflow = current_len + len(nxt) > self.max_chunk_chars
            if hit_topic_shift or would_overflow:
                chunks.append(" ".join(current).strip())
                current = [nxt]
            else:
                current.append(nxt)
        if current:
            chunks.append(" ".join(current).strip())
        return [c for c in chunks if c]

    # -- helpers --
    @staticmethod
    def _split_sentences(text: str) -> List[str]:
        normalised = re.sub(r'\s+', ' ', text).strip()
        parts = _SENTENCE_BOUNDARY.split(normalised)
        return [p.strip() for p in parts if p.strip()]

    @staticmethod
    def _cosine_distance(a: List[float], b: List[float]) -> float:
        dot = sum(x * y for x, y in zip(a, b))
        na = math.sqrt(sum(x * x for x in a))
        nb = math.sqrt(sum(y * y for y in b))
        if na == 0 or nb == 0:
            return 0.0
        return 1.0 - dot / (na * nb)

    @staticmethod
    def _percentile(values: List[float], pct: int) -> float:
        if not values:
            return 0.0
        ordered = sorted(values)
        k = (len(ordered) - 1) * (pct / 100.0)
        lo = int(math.floor(k))
        hi = int(math.ceil(k))
        if lo == hi:
            return ordered[lo]
        return ordered[lo] + (ordered[hi] - ordered[lo]) * (k - lo)

    def _fallback(self, text: str) -> List[str]:
        return [c for c in self.fallback_splitter.split_text(text) if c.strip()]


class DocumentProcessor:
    def __init__(self, embeddings: Any = None):
        self.fallback_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000, chunk_overlap=200, length_function=len,
            separators=["\n\n", "\n", " ", ""],
        )
        # Reuse the vector store's embeddings when provided so chunking and
        # indexing share one model; otherwise create the standard fallback ladder.
        if embeddings is None:
            from services.embedding_fallback import FallbackEmbeddings
            embeddings = FallbackEmbeddings()
        self.text_splitter = SemanticChunker(
            embeddings, fallback_splitter=self.fallback_splitter
        )

    def process_pdf(self, file_path: str) -> List[Document]:
        """Process a PDF file and return semantically-chunked document pieces."""
        try:
            reader = PdfReader(file_path)
            documents = []

            for page_num, page in enumerate(reader.pages):
                text = page.extract_text()

                if text and text.strip():
                    doc = Document(
                        page_content=text,
                        metadata={
                            "source": os.path.basename(file_path),
                            "page": page_num + 1,
                            "total_pages": len(reader.pages)
                        }
                    )
                    documents.append(doc)

            chunks = self.text_splitter.split_documents(documents)
            return chunks

        except Exception as e:
            raise Exception(f"Error processing PDF: {str(e)}")

    def extract_metadata(self, file_path: str) -> dict:
        """Extract metadata from PDF"""
        try:
            reader = PdfReader(file_path)
            metadata = reader.metadata

            return {
                "title": metadata.get("/Title", "Unknown"),
                "author": metadata.get("/Author", "Unknown"),
                "pages": len(reader.pages),
                "file_size": os.path.getsize(file_path)
            }
        except Exception as e:
            return {"error": str(e)}

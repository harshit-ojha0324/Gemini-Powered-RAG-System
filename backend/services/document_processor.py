import logging
import os
import re
import math
import statistics
from typing import List, Any

from pypdf import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document

logger = logging.getLogger(__name__)

# Split on sentence-ending punctuation followed by whitespace and a capital/quote/digit.
_SENTENCE_BOUNDARY = re.compile(r'(?<=[.!?])\s+(?=[A-Z0-9"\'])')

BREAKPOINT_PERCENTILE = 90  # a gap in the top 10% of sentence distances is a topic shift
MIN_CHUNK_CHARS = 250
MAX_CHUNK_CHARS = 1500
MAX_SENTENCES = 400  # beyond this, one embedding per sentence isn't worth it


def cosine(a: List[float], b: List[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


class SemanticChunker:
    """Embedding-similarity ("semantic") chunker.

    Instead of cutting text at a fixed character count, this splits the text into
    sentences, embeds each sentence, and starts a new chunk wherever the cosine
    distance between two consecutive sentences rises above a percentile threshold
    — i.e. at a topic shift. Chunks therefore follow the document's semantics
    rather than an arbitrary window.

    It degrades gracefully to recursive character splitting when there aren't
    enough sentences to reason about or when embeddings are unavailable.
    """

    def __init__(self, embeddings: Any):
        self.embeddings = embeddings
        self.fallback_splitter = RecursiveCharacterTextSplitter(chunk_size=1000)

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
        if len(text) <= MIN_CHUNK_CHARS:
            return [text]

        normalised = re.sub(r'\s+', ' ', text)
        sentences = [s.strip() for s in _SENTENCE_BOUNDARY.split(normalised) if s.strip()]
        # Too few sentences to reason about a topic shift, or so many that the
        # per-sentence embedding pass isn't worth it — fall back to char splitting.
        if len(sentences) < 3 or len(sentences) > MAX_SENTENCES:
            return self._fallback(text)

        try:
            vectors = self.embeddings.embed_documents(sentences)
        except Exception as e:
            # Say so: otherwise a quota or key problem quietly turns semantic
            # chunking into fixed-size splitting.
            logger.warning(f"Sentence embedding failed ({e}); using character splitting for this page")
            return self._fallback(text)

        distances = [1.0 - cosine(vectors[i], vectors[i + 1]) for i in range(len(vectors) - 1)]
        threshold = statistics.quantiles(distances, n=100, method="inclusive")[BREAKPOINT_PERCENTILE - 1]

        chunks: List[str] = []
        current = [sentences[0]]
        for i, dist in enumerate(distances):
            nxt = sentences[i + 1]
            current_len = sum(len(s) + 1 for s in current)
            hit_topic_shift = dist >= threshold and current_len >= MIN_CHUNK_CHARS
            would_overflow = current_len + len(nxt) > MAX_CHUNK_CHARS
            if hit_topic_shift or would_overflow:
                chunks.append(" ".join(current).strip())
                current = [nxt]
            else:
                current.append(nxt)
        if current:
            chunks.append(" ".join(current).strip())
        return [c for c in chunks if c]

    def _fallback(self, text: str) -> List[str]:
        return [c for c in self.fallback_splitter.split_text(text) if c.strip()]


class DocumentProcessor:
    def __init__(self, embeddings: Any):
        # The vector store's embeddings, so chunking and indexing share one model.
        self.text_splitter = SemanticChunker(embeddings)

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

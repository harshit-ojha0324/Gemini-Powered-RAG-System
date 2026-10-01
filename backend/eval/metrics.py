"""Metric helpers for the RAG retrieval & grounding eval."""
from typing import Any, Dict, List, Tuple

from services.document_processor import cosine

_ABSTAIN_MARKERS = [
    "don't have enough information", "do not have enough information",
    "not enough information", "cannot find", "can't find", "no information",
    "not in the documents", "don't know", "do not know", "unable to answer",
    "no relevant information",
]


class InMemoryRetriever:
    """Cosine top-k retriever over the eval corpus, using the production
    FallbackEmbeddings — the same embedding model the app indexes with, so the
    retrieval quality measured here reflects the real system."""

    def __init__(self, embeddings: Any, corpus: List[Dict]):
        self.embeddings = embeddings
        self.ids = [c["id"] for c in corpus]
        self.texts = [c["text"] for c in corpus]
        self.vectors = embeddings.embed_documents(self.texts)

    def retrieve(self, query: str, k: int = 4) -> List[Tuple[str, str, float]]:
        qv = self.embeddings.embed_query(query)
        scored = [
            (self.ids[i], self.texts[i], cosine(qv, self.vectors[i]))
            for i in range(len(self.ids))
        ]
        scored.sort(key=lambda t: t[2], reverse=True)
        return scored[:k]


def context_scores(retrieved: List[Tuple[str, str, float]], relevant_ids: List[str]) -> Dict:
    """Context-relevance scores for one question."""
    retrieved_ids = [r[0] for r in retrieved]
    relevant = set(relevant_ids)
    hits = [rid for rid in retrieved_ids if rid in relevant]
    precision = len(hits) / len(retrieved_ids) if retrieved_ids else 0.0
    recall = len(set(hits)) / len(relevant) if relevant else 0.0
    return {
        "hit": 1.0 if hits else 0.0,
        "precision": precision,
        "recall": recall,
        "top_score": retrieved[0][2] if retrieved else 0.0,
    }


def is_abstention(text: str) -> bool:
    t = (text or "").lower()
    return any(m in t for m in _ABSTAIN_MARKERS)


def substring_in_contexts(substr: str, contexts: List[str]) -> bool:
    s = (substr or "").lower()
    if not s:
        return False
    return any(s in c.lower() for c in contexts)


def answer_faithfulness(answer: str, contexts: List[str], embeddings: Any) -> float:
    """Max cosine similarity between the answer and any retrieved passage.
    A faithful answer restates its supporting context, so higher == more grounded."""
    if not answer or not contexts:
        return 0.0
    av = embeddings.embed_query(answer)
    cvs = embeddings.embed_documents(contexts)
    return max((cosine(av, cv) for cv in cvs), default=0.0)

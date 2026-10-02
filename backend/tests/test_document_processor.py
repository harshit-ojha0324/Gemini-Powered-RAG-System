from services.document_processor import SemanticChunker

APPLE = "Apples grow on trees in temperate orchards and are picked every autumn by hand."
ROCKET = "Rockets burn liquid fuel and oxygen to lift satellites into a stable low orbit."


class TopicEmbeddings:
    """Two orthogonal 'topics', so the only semantic shift is apple -> rocket."""
    def embed_documents(self, texts):
        return [[1.0, 0.0] if "Apples" in t else [0.0, 1.0] for t in texts]


def test_semantic_chunker_splits_at_the_topic_shift():
    text = " ".join([APPLE] * 4 + [ROCKET] * 4)
    chunks = SemanticChunker(TopicEmbeddings()).split_text(text)
    assert chunks == [" ".join([APPLE] * 4), " ".join([ROCKET] * 4)]


def test_semantic_chunker_falls_back_when_embedding_fails(caplog):
    class Broken:
        def embed_documents(self, texts):
            raise RuntimeError("no embeddings")

    text = " ".join([APPLE] * 4 + [ROCKET] * 4)
    chunks = SemanticChunker(Broken()).split_text(text)
    assert chunks and all(len(c) <= 1000 for c in chunks)
    assert "no embeddings" in caplog.text

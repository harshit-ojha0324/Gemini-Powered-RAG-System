"""Regression tests for the Tier-0 hardening: path containment, a single
vector-store instance, and a loud (never silent) embedding failure."""

import os
from pathlib import Path
from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient

import app as app_module
from app import app, resolve_document_path, DOCUMENTS_DIR
from services.embedding_fallback import FallbackEmbeddings

client = TestClient(app)


# --- path containment -------------------------------------------------------

@pytest.mark.parametrize("hostile", [
    "../secret.pdf",
    "../../etc/passwd",
    "/etc/passwd",
    "..",
    ".",
    "",
    "sub/../../escape.pdf",
])
def test_resolve_document_path_rejects_escapes(hostile):
    """Nothing a client sends may resolve outside the documents directory."""
    from fastapi import HTTPException
    try:
        resolved = resolve_document_path(hostile)
    except HTTPException as exc:
        assert exc.status_code == 400
    else:
        # If it resolved at all, it must be contained.
        assert resolved.parent == DOCUMENTS_DIR


def test_resolve_document_path_accepts_plain_name():
    assert resolve_document_path("report.pdf") == DOCUMENTS_DIR / "report.pdf"


def test_delete_route_traversal_is_unreachable_over_http():
    """Starlette's router already rejects every encoding of a traversing
    filename here (a path parameter never matches across '/'), so this route
    was not the arbitrary-delete hole it looks like. resolve_document_path is
    defence in depth for any non-HTTP caller of the same handler."""
    victim = DOCUMENTS_DIR.parent / "do-not-delete.txt"
    victim.write_text("still here")
    try:
        for hostile in ["../do-not-delete.txt", "..%2Fdo-not-delete.txt", ".."]:
            response = client.delete(f"/api/documents/{quote(hostile, safe='')}")
            assert response.status_code in (400, 404)
            assert victim.exists(), f"{hostile} deleted a file outside the documents dir"
    finally:
        victim.unlink(missing_ok=True)


@pytest.mark.parametrize("hostile_name", ["../evil.pdf", "../../evil-deep.pdf"])
def test_upload_never_writes_outside_documents_dir(hostile_name):
    """The upload filename arrives in the multipart body, so no router
    normalisation applies — this one really did escape before the fix.
    The bogus PDF may fail to parse; what matters is where it landed."""
    escaped = (DOCUMENTS_DIR / hostile_name).resolve()  # where the old code wrote
    contained = DOCUMENTS_DIR / Path(hostile_name).name
    assert escaped.parent != DOCUMENTS_DIR, "test target must be outside the docs dir"
    try:
        client.post(
            "/api/upload",
            files={"file": (hostile_name, b"%PDF-1.4 not really a pdf", "application/pdf")},
        )
        assert not escaped.exists(), f"{hostile_name} escaped to {escaped}"
    finally:
        escaped.unlink(missing_ok=True)
        contained.unlink(missing_ok=True)


# --- one vector store -------------------------------------------------------

def test_agent_and_api_share_one_vectorstore():
    """Two instances made /api/reset-embeddings report success on a store
    the query path never reads."""
    assert app_module.rag_agent.vectorstore_service is app_module.vectorstore_service


# --- embeddings fail loudly -------------------------------------------------

def _fallback_with_broken_local_model(monkeypatch):
    import langchain_community.embeddings as lc_embeddings

    def _explode(*args, **kwargs):
        raise RuntimeError("simulated HuggingFace load failure")

    monkeypatch.setattr(lc_embeddings, "HuggingFaceEmbeddings", _explode, raising=False)
    embeddings = FallbackEmbeddings()
    embeddings.use_fallback = True
    embeddings.fallback_embeddings = None
    return embeddings


def test_broken_local_model_raises_instead_of_faking_vectors(monkeypatch):
    embeddings = _fallback_with_broken_local_model(monkeypatch)
    with pytest.raises(RuntimeError, match="No usable embedding model"):
        embeddings.embed_query("anything")


def test_gemini_failure_switches_to_local_model():
    class Gemini:
        def embed_query(self, text):
            raise RuntimeError("429 quota exceeded")

    class Local:
        def embed_query(self, text):
            return [1.0]

    embeddings = FallbackEmbeddings()
    embeddings.primary_embeddings = Gemini()
    embeddings.fallback_embeddings = Local()
    assert embeddings.embed_query("anything") == [1.0]
    assert embeddings.mode == "local" and embeddings.is_degraded
    embeddings.reset_to_primary()
    assert embeddings.mode == "gemini"


def test_health_reports_embedding_mode():
    response = client.get("/api/health")
    assert response.status_code == 200
    services = response.json()["services"]
    assert services["embedding_mode"] in {"gemini", "local"}

# Backend notes

## Telemetry

Chroma's anonymized telemetry is off by default (`services/vectorstore.py` sets `ANONYMIZED_TELEMETRY=False` unless the environment already sets it). To re-enable it, set `ANONYMIZED_TELEMETRY=True` before starting the server. `posthog` is pinned below 6 because chromadb 0.4.22 uses the older `capture()` signature.

## Gemini / Embeddings

`EMBEDDING_MODEL` picks the embedding model once, at startup: `local` for the offline sentence-transformers model, or a Gemini embedding model name. Unset, it is `models/gemini-embedding-001` when `GEMINI_API_KEY` is set and `local` otherwise.

There is no runtime fallback between models: their vectors differ in size and space, so each model has its own Chroma collection, which `sync_index()` in `app.py` reconciles with the PDFs on disk at every startup.

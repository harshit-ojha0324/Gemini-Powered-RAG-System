# Backend notes

## Telemetry

Chroma's anonymized telemetry is off by default (`services/vectorstore.py` sets `ANONYMIZED_TELEMETRY=False` unless the environment already sets it). To re-enable it, set `ANONYMIZED_TELEMETRY=True` before starting the server. `posthog` is pinned below 6 because chromadb 0.4.22 uses the older `capture()` signature.

## Gemini / Embeddings

The Gemini embedding model is configurable via environment or the application config:

- Environment variable: `GEMINI_MODEL`
- Pydantic config: `gemini_model` in `backend/config.py` (defaults to `models/gemini-2.0-flash-exp`)

If the configured Gemini model is not available or initialization fails, the service automatically falls back to local HuggingFace embeddings.

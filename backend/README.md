# Backend notes

## Telemetry

The project disables Chroma/ChromA telemetry by default to avoid runtime errors caused by mismatched `posthog` API signatures in some runtime environments. To re-enable telemetry, set the environment variable `CHROMA_TELEMETRY=true` before starting the server.

## Gemini / Embeddings

The Gemini embedding model is configurable via environment or the application config:

- Environment variable: `GEMINI_MODEL`
- Pydantic config: `gemini_model` in `backend/config.py` (defaults to `models/gemini-2.0-flash-exp`)

If the configured Gemini model is not available or initialization fails, the service automatically falls back to local HuggingFace embeddings.

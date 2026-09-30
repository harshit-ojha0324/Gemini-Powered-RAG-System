# LLM Document Agent

A full-stack **Retrieval-Augmented Generation (RAG)** application that lets you upload PDF documents and ask questions about them using Google Gemini AI. Built with enterprise-grade security features including PII detection, injection prevention, and real-time security monitoring.

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Local Development](#local-development)
  - [Docker Deployment](#docker-deployment)
- [Configuration](#configuration)
- [API Reference](#api-reference)
- [Security](#security)
- [Testing](#testing)
- [Project Structure](#project-structure)
- [Troubleshooting](#troubleshooting)

---

## Overview

LLM Document Agent enables intelligent question-answering over your PDF documents. Upload any PDF, ask natural language questions, and get contextual answers grounded in your document content — with full source attribution showing which page the answer came from.

The system uses a RAG pipeline:
1. PDFs are parsed and split into **semantically-coherent chunks** (sentences are embedded and split at topic-shift breakpoints, with a recursive-character fallback)
2. Chunks are embedded into a vector database (Chroma) using Google Gemini embeddings
3. At query time, semantically similar chunks are retrieved and passed to the LLM as context
4. Gemini 2.0 Flash generates a grounded, accurate response

Conversation history is maintained so you can ask follow-up questions naturally.

---

## Features

### Core
- **PDF Upload & Management** — Upload, list, and delete documents via a clean web UI
- **Semantic Chunking** — Documents are split at embedding-distance topic shifts rather than fixed-size windows, so each chunk stays on one idea (`services/document_processor.py`)
- **Semantic Search** — Vector similarity search over document chunks using Chroma
- **RAG-Powered Q&A** — Contextual answers from Google Gemini, grounded in your documents
- **Source Attribution** — Every answer links back to the source document and page number
- **Conversation Memory** — Multi-turn conversations with maintained chat history
- **Embedding Fallback** — Automatically falls back to HuggingFace embeddings if Gemini quota is exceeded

### Security
- **PII Detection** — Identifies emails, phone numbers, SSNs, and credit card numbers using Microsoft Presidio (with regex fallback)
- **Injection Prevention** — Detects and blocks SQL injection, prompt injection, and XSS attacks in user input
- **Output Content Filtering** — Redacts API keys, passwords, and tokens from LLM responses before they reach the user
- **Security Audit Logging** — All security incidents are logged with timestamps for review
- **Security Dashboard** — Real-time monitoring UI showing incident counts, PII detections, and recent events

### Developer Experience
- **Auto-generated API Docs** — Swagger UI at `/docs` and ReDoc at `/redoc`
- **Docker Support** — One-command deployment with Docker Compose
- **Makefile Shortcuts** — Common tasks available as `make` commands
- **Test Suite** — Pytest with coverage reporting (note: three of the six backend test modules are still empty placeholder stubs)

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Frontend (React + Vite)               │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────┐  │
│  │ DocumentUpload│  │ChatInterface │  │SecurityDashbrd│  │
│  └──────┬───────┘  └──────┬───────┘  └───────┬───────┘  │
└─────────┼─────────────────┼──────────────────┼──────────┘
          │                 │                  │  HTTP/REST
          ▼                 ▼                  ▼
┌─────────────────────────────────────────────────────────┐
│                  Backend (FastAPI)                       │
│                                                         │
│  ┌────────────────────────────────────────────────────┐ │
│  │                Security Layer                      │ │
│  │  PII Detector │ Input Validator │ Content Filter   │ │
│  └────────────────────────────────────────────────────┘ │
│                          │                              │
│  ┌───────────────────────┼───────────────────────────┐  │
│  │              RAG Agent (LangChain)                │  │
│  │                       │                           │  │
│  │  ┌────────────────────┴─────────────────────┐    │  │
│  │  │         Document Processor               │    │  │
│  │  │  PDF Parsing → Chunking → Embedding      │    │  │
│  │  └────────────────────┬─────────────────────┘    │  │
│  │                       │                           │  │
│  │  ┌────────────────────┴─────────────────────┐    │  │
│  │  │           Vector Store (Chroma)          │    │  │
│  │  │  Persist & Retrieve Semantic Embeddings  │    │  │
│  │  └──────────────────────────────────────────┘    │  │
│  └───────────────────────────────────────────────────┘  │
│                          │                              │
│              Google Gemini API                          │
│         (Embeddings + Text Generation)                  │
└─────────────────────────────────────────────────────────┘
```

### Data Flow

1. **Upload**: User uploads a PDF → FastAPI saves it → `DocumentProcessor` parses and chunks the text → chunks embedded via Gemini → stored in Chroma
2. **Query**: User sends a question → Security layer validates input → RAG agent retrieves top-k relevant chunks → Gemini generates answer with source citations → Content filter scans output → Response returned to UI

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 18, Vite, Axios, Lucide React |
| Backend | Python 3.9+, FastAPI, Uvicorn |
| LLM | Google Gemini 2.0 Flash (`langchain-google-genai`) |
| Embeddings | Gemini Embeddings (HuggingFace fallback) |
| Vector Store | ChromaDB 0.4 |
| LLM Orchestration | LangChain 0.1 |
| PDF Parsing | PyPDF 4.0 |
| PII Detection | Microsoft Presidio (spaCy `en_core_web_lg`) |
| Data Validation | Pydantic |
| Testing | pytest, pytest-cov |
| Containerization | Docker, Docker Compose |

---

## Getting Started

### Prerequisites

- **Python** 3.9 or higher
- **Node.js** 18 or higher
- **Google Gemini API Key** — Get one free at [aistudio.google.com](https://aistudio.google.com/app/apikey)

### Local Development

**1. Clone the repository**

```bash
git clone <repository-url>
cd llm-document-agent
```

**2. Run the setup script**

This creates a Python virtual environment, installs all backend and frontend dependencies, and downloads the required spaCy NLP model.

```bash
bash setup.sh
```

**3. Configure your API key**

```bash
cp .env.example backend/.env
# Open backend/.env and set your key:
# GEMINI_API_KEY=your_key_here
```

**4. Start the application**

```bash
bash start.sh
```

The application will be available at:

| Service | URL |
|---|---|
| Frontend | http://localhost:5173 |
| Backend API | http://localhost:8000 |
| Swagger Docs | http://localhost:8000/docs |
| ReDoc | http://localhost:8000/redoc |

### Docker Deployment

**1. Configure environment**

```bash
cp .env.example .env
# Set GEMINI_API_KEY in .env
```

**2. Start with Docker Compose**

```bash
bash start-docker.sh
# or
make docker-start
```

**3. Stop containers**

```bash
make docker-stop
```

**About the backend image**

`backend/Dockerfile` is a two-stage build: dependencies are installed into a virtualenv in a builder stage, and only that virtualenv plus the app code are copied into the runtime image. The runtime image:

- runs as a non-root user (UID/GID 1000 by default, override with `--build-arg APP_UID=... --build-arg APP_GID=...`)
- installs the CPU-only PyTorch build, since the fallback embeddings run on CPU (use `--build-arg TORCH_INDEX_URL=https://pypi.org/simple` for the CUDA build)
- has a `HEALTHCHECK` against `/api/health`

CI builds the image and waits for it to report healthy on every push and pull request to `main`. To build it on its own:

```bash
docker build -t rag-backend backend
```

### Makefile Commands

```bash
make setup        # Run initial setup
make start        # Start locally
make stop         # Stop local services
make test         # Run test suite with coverage
make clean        # Remove venvs and caches
make install      # Install dependencies only
make docker-start # Start with Docker
make docker-stop  # Stop Docker containers
```

---

## Configuration

All configuration is managed via environment variables. Copy `.env.example` to `backend/.env` and adjust as needed.

| Variable | Default | Description |
|---|---|---|
| `GEMINI_API_KEY` | *(required)* | Your Google Gemini API key |
| `GEMINI_MODEL` | `models/embedding-001` | Gemini **embedding** model (the generation model is fixed to `gemini-2.0-flash` in `rag_agent.py`, not controlled by this variable) |
| `CHROMA_PERSIST_DIRECTORY` | `./data/vectorstore` | Path to persist the Chroma vector DB |
| `DOCUMENTS_DIRECTORY` | `./data/documents` | Path to store uploaded PDF files |
| `LOGS_DIRECTORY` | `./data/logs` | Path to store security event logs |
| `MAX_FILE_SIZE_MB` | `10` | Maximum allowed upload file size |
| `ALLOWED_EXTENSIONS` | `pdf` | Comma-separated list of allowed file extensions |
| `CHROMA_TELEMETRY` | `false` | Enable/disable Chroma anonymized telemetry |
| `DEBUG` | `true` | Enable debug mode |

---

## API Reference

### Document Management

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/upload` | Upload a PDF document |
| `GET` | `/api/documents` | List all uploaded documents |
| `DELETE` | `/api/documents/{filename}` | Delete a document and its embeddings |

### Query & Chat

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/query` | Submit a question (with security checks) |
| `GET` | `/api/stats` | Get system statistics (docs, queries, incidents) |
| `GET` | `/api/health` | Health check endpoint |

### Security & Administration

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/security/logs` | Retrieve security incident logs (last 50 by default) |
| `POST` | `/api/reset-embeddings` | Reset to Gemini embeddings after quota recovery |

#### Query Request Body

```json
{
  "question": "What is the main topic of the document?",
  "document_name": "optional-specific-document.pdf"
}
```

#### Query Response

```json
{
  "answer": "The document covers...",
  "sources": [
    { "document": "report.pdf", "page": 3 }
  ],
  "security_flags": [],
  "conversation_id": "abc123"
}
```

Full interactive API documentation is available at `/docs` when the backend is running.

---

## Security

This application implements a multi-layer security architecture to protect both users and the system.

### Input Validation

All user queries pass through `InputValidator` before reaching the LLM:
- **SQL Injection** — Detects `DROP TABLE`, `SELECT *`, `UNION SELECT`, and similar patterns
- **Prompt Injection** — Detects attempts to override system instructions (e.g., "ignore previous instructions")
- **XSS** — Detects `<script>`, `javascript:`, and similar vectors

Flagged queries are blocked and logged before any LLM processing occurs.

### Instruction Hierarchy

The RAG prompt enforces an explicit instruction hierarchy: the system rules sit above the retrieved document context and the user question, both of which are wrapped in delimiters and treated as untrusted **data**, never as instructions. Injection-style text embedded in a document or question is to be reported, not obeyed — the in-prompt complement to the regex gate above (`agents/prompt_templates.py`).

### PII Redaction

Detected PII is redacted (`security/pii_detector.py`) before the query is written to the audit log or forwarded to Gemini, so raw PII never leaves the process. (Injection attempts are logged verbatim on purpose, for forensics.)

### PII Detection

The `PIIDetector` scans both user inputs and LLM outputs for:
- Email addresses
- Phone numbers
- Social Security Numbers
- Credit card numbers

Detection uses Microsoft Presidio (with spaCy NER) when available, with a regex-based fallback. Detections are flagged in the response and logged as security incidents.

### Output Content Filtering

`ContentFilter` scans LLM responses and redacts any accidental exposure of:
- API keys and tokens
- Passwords and credentials
- Private keys

### Security Dashboard

The frontend Security Dashboard provides:
- Total incident count and PII detection count
- Breakdown of incident types
- Timestamped log of recent security events

### Security Logging

All security incidents are written to `data/logs/security_events.jsonl` with the following structure:

```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "event_type": "pii_detected",
  "severity": "medium",
  "details": { "pii_types": ["EMAIL"] }
}
```

---

## Testing

Run the full test suite with coverage:

```bash
bash run-tests.sh
# or
make test
```

This runs all tests under `backend/tests/` and generates an HTML coverage report at `backend/htmlcov/index.html`.

To run tests directly with pytest:

```bash
cd backend
source venv/bin/activate
pytest tests/ -v --cov=. --cov-report=html
```

### Retrieval & Grounding Evaluation

Beyond unit tests, a retrieval-evaluation harness (`backend/eval/`) measures the RAG pipeline against a labelled gold set:

```bash
make eval
# or: cd backend && python -m eval.run_eval --k 4 --threshold 0.7
```

It reports **context relevance** (does retrieval surface the passage that holds the answer?) and **grounded-response rate** (are answerable questions answered from context, and are out-of-scope questions correctly abstained on?). It runs offline on the local MiniLM embeddings — no API key needed — and gates on a threshold so it can run in CI. Add `--generate` with a valid `GEMINI_API_KEY` to score answer faithfulness on the model's real responses.

---

## Project Structure

```
llm-document-agent/
├── backend/
│   ├── agents/
│   │   ├── rag_agent.py           # Core RAG pipeline (retrieval + generation)
│   │   └── prompt_templates.py    # System and user prompt templates
│   ├── services/
│   │   ├── document_processor.py  # PDF parsing and text chunking
│   │   ├── vectorstore.py         # Chroma vector DB wrapper
│   │   ├── embedding_fallback.py  # Gemini/HuggingFace embedding with fallback
│   │   ├── llm_service.py         # LLM service abstraction
│   │   └── telemetry_shim.py      # Chroma telemetry compatibility shim
│   ├── security/
│   │   ├── pii_detector.py        # PII detection (Presidio + regex)
│   │   ├── input_validator.py     # Injection and XSS detection
│   │   └── content_filter.py      # Output sensitive data redaction
│   ├── tests/                     # pytest test suite
│   ├── app.py                     # FastAPI application and route definitions
│   ├── config.py                  # Pydantic settings (reads from .env)
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx                # Root component with sidebar navigation
│   │   ├── components/
│   │   │   ├── ChatInterface.jsx  # Q&A chat UI
│   │   │   ├── DocumentUpload.jsx # Upload and document list management
│   │   │   ├── MessageBubble.jsx  # Individual chat message rendering
│   │   │   └── SecurityDashboard.jsx # Security metrics and incident log
│   │   └── services/
│   │       └── api.js             # Axios API client (all backend calls)
│   ├── package.json
│   └── vite.config.js
│
├── data/
│   ├── documents/                 # Uploaded PDFs (persisted)
│   ├── vectorstore/               # Chroma vector database (persisted)
│   └── logs/                     # Security event logs (persisted)
│
├── docker-compose.yml
├── Makefile
├── setup.sh
├── start.sh
├── start-docker.sh
├── run-tests.sh
└── .env.example
```

---

## Troubleshooting

**Gemini API quota exceeded**

The embedding service will automatically fall back to HuggingFace sentence-transformers. Once your quota resets, call `POST /api/reset-embeddings` to switch back to Gemini embeddings.

**spaCy model not found**

If PII detection fails with a model error, run:
```bash
python -m spacy download en_core_web_lg
```

**Chroma version conflicts**

This project pins `chromadb==0.4.22`. Do not upgrade without testing, as the Chroma API changed significantly in 0.5+.

**Port already in use**

Check for existing processes on ports 8000 (backend) and 5173 (frontend):
```bash
lsof -i :8000
lsof -i :5173
```

**Docker: environment variables not picked up**

Ensure your `.env` file is in the project root (not `backend/.env`) when running Docker Compose, as `docker-compose.yml` reads from the project root.

**Docker: permission denied writing to `data/` (Linux)**

The backend container runs as UID 1000, not root. If `data/` was created by an older image that ran as root, or your host user has a different UID, either give the directory to UID 1000 (`sudo chown -R 1000:1000 data`) or rebuild with your own IDs (`--build-arg APP_UID=$(id -u) --build-arg APP_GID=$(id -g)`). Docker Desktop on macOS usually maps file ownership for you, so this mostly affects Linux hosts.

from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional
from collections import deque
import os
import shutil
import threading
from datetime import datetime
import json
import logging
from pathlib import Path
from dotenv import load_dotenv

# Load backend/.env before the services below read their settings.
load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from agents.rag_agent import RAGAgent
from security.pii_detector import PIIDetector
from security.input_validator import InputValidator
from security.content_filter import ContentFilter
from services.document_processor import DocumentProcessor
from services.vectorstore import VectorStoreService

app = FastAPI(title="Smart Document Q&A Agent", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services.
# One VectorStoreService for the whole process: the agent queries the same
# store (and embedding model) the upload path writes to.
vectorstore_service = VectorStoreService()
rag_agent = RAGAgent(vectorstore_service=vectorstore_service)
pii_detector = PIIDetector()
input_validator = InputValidator()
content_filter = ContentFilter()
# Share the vector store's embeddings so semantic chunking and indexing use one model.
document_processor = DocumentProcessor(embeddings=vectorstore_service.embeddings)

# Ensure directories exist
DOCUMENTS_DIR = Path("./data/documents").resolve()
DOCUMENTS_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = Path("./data/logs/security_log.jsonl")
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
MAX_UPLOAD_BYTES = 10 * 1024 * 1024
# Routes that do blocking work (PDF parsing, Presidio, Chroma, Gemini) are
# plain `def`, so FastAPI runs them in its threadpool instead of stalling the
# event loop. Changes to one document's file + chunks must not interleave.
# ponytail: one lock for all uploads/deletes; per-filename locks if uploads get busy.
index_lock = threading.Lock()


def pdf_files() -> List[Path]:
    """Uploaded PDFs, whatever the case of the extension."""
    return [f for f in DOCUMENTS_DIR.iterdir() if f.suffix.lower() == ".pdf"]


def resolve_document_path(filename: str) -> Path:
    """Map a client-supplied filename to a path inside DOCUMENTS_DIR.

    The client string is never used as a path. We take its basename and then
    assert the resolved result is still contained in the documents directory,
    so '../', absolute paths and symlink tricks cannot escape.
    """
    basename = Path(filename or "").name
    if not basename or basename in {".", ".."}:
        raise HTTPException(status_code=400, detail="Invalid filename")

    candidate = (DOCUMENTS_DIR / basename).resolve()
    if candidate.parent != DOCUMENTS_DIR:
        raise HTTPException(status_code=400, detail="Invalid filename")
    return candidate


def sync_index():
    """Make the active model's index match the PDFs on disk.

    The PDFs are the source of truth and every embedding model has its own
    index, so this indexes files the current one hasn't seen (e.g. after
    switching EMBEDDING_MODEL) and drops chunks of files deleted since.
    """
    # ponytail: synchronous at startup; move to a background task if libraries get large.
    on_disk = {f.name: f for f in pdf_files()}
    indexed = vectorstore_service.indexed_sources()
    for name in indexed - on_disk.keys():
        vectorstore_service.delete_document(name)
    for name in sorted(on_disk.keys() - indexed):
        try:
            vectorstore_service.add_documents(document_processor.process_pdf(str(on_disk[name])), name)
            logger.info(f"Indexed {name} with {vectorstore_service.embedding_model}")
        except Exception as e:
            # Keep starting up; the file stays listed but unsearchable until re-uploaded.
            logger.warning(f"Could not index {name}: {e}")


sync_index()

# Bounds on what one request can make us redact, embed and send to the LLM.
MAX_QUESTION_CHARS = 10_000
MAX_HISTORY_MESSAGES = 10

# Request/Response Models
class QueryRequest(BaseModel):
    question: str = Field(max_length=MAX_QUESTION_CHARS)
    conversation_history: Optional[List[dict]] = []

class QueryResponse(BaseModel):
    answer: str
    sources: List[dict]
    security_warnings: List[str]

# Global stats
stats = {
    "total_queries": 0,
    "security_incidents": 0,
    "pii_detections": 0
}

def log_security_incident(query: str, flags: List[str], pii_found: bool):
    """Log security incidents to file"""
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "query": query,
        "flags": flags,
        "pii_detected": pii_found
    }
    
    try:
        with open(LOG_FILE, "a") as f:
            f.write(json.dumps(log_entry) + "\n")
    except Exception:
        pass  # Don't let logging failures break the request
    
    stats["security_incidents"] += 1
    if pii_found:
        stats["pii_detections"] += 1

@app.get("/")
async def root():
    return {"message": "Smart Document Q&A Agent API", "status": "running"}

@app.post("/api/upload")
def upload_document(file: UploadFile = File(...)):
    """Upload and process a PDF document"""
    try:
        if not file.filename or not file.filename.lower().endswith(".pdf"):
            raise HTTPException(status_code=400, detail="Only PDF files are allowed")

        file.file.seek(0, os.SEEK_END)
        if file.file.tell() > MAX_UPLOAD_BYTES:
            raise HTTPException(status_code=413, detail=f"PDFs are limited to {MAX_UPLOAD_BYTES // 2**20} MB")
        file.file.seek(0)

        # Never write to a client-controlled path.
        resolved = resolve_document_path(file.filename)
        safe_name = resolved.name
        # Stage under a name the document list ignores, and only move it into
        # place once it is indexed: a PDF that fails to parse never shows up as
        # uploaded, and a failed re-upload leaves the previous version intact.
        partial = resolved.with_name(safe_name + ".part")
        with index_lock:
            try:
                with open(partial, "wb") as buffer:
                    shutil.copyfileobj(file.file, buffer)
                documents = document_processor.process_pdf(str(partial))
                vectorstore_service.add_documents(documents, safe_name)
                os.replace(partial, resolved)
            finally:
                partial.unlink(missing_ok=True)

        return {
            "message": "Document uploaded and processed successfully",
            "filename": safe_name,
            "chunks": len(documents),
            "status": "success"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing document: {str(e)}")

@app.post("/api/query", response_model=QueryResponse)
def query_documents(request: QueryRequest):
    """Query documents with security checks"""
    try:
        stats["total_queries"] += 1
        security_warnings = []
        
        # Redact PII first, so it reaches neither the audit log nor the LLM.
        safe_question, pii_types = pii_detector.redact(request.question)
        if pii_types:
            security_warnings.append(f"PII detected and redacted: {', '.join(pii_types)}")
            log_security_incident(safe_question, ["PII_DETECTED"], True)

        validation_result = input_validator.validate(safe_question)
        if not validation_result["is_valid"]:
            security_warnings.extend(validation_result["warnings"])
            log_security_incident(safe_question, validation_result["warnings"], False)

        if any(w.startswith("INJECTION") for w in security_warnings):
            raise HTTPException(status_code=400, detail="Query blocked due to security concerns")

        # Earlier turns reach the LLM too (to condense the follow-up question),
        # and the client sends them as typed, so they get the same redaction.
        history = [
            {**msg, "content": pii_detector.redact(str(msg.get("content", ""))[:MAX_QUESTION_CHARS])[0]}
            for msg in (request.conversation_history or [])[-MAX_HISTORY_MESSAGES:]
        ]
        result = rag_agent.query(safe_question, history)
        filtered_answer = content_filter.filter(result["answer"])
        
        return QueryResponse(
            answer=filtered_answer,
            sources=result["sources"],
            security_warnings=security_warnings
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")

@app.get("/api/documents")
def list_documents():
    """List all uploaded documents"""
    try:
        documents = [
            {
                "filename": f.name,
                "size": f.stat().st_size,
                "uploaded_at": datetime.fromtimestamp(f.stat().st_mtime).isoformat()
            }
            for f in pdf_files()
        ]
        return {"documents": documents, "count": len(documents)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/documents/{filename}")
def delete_document(filename: str):
    """Delete a document"""
    try:
        file_path = resolve_document_path(filename)
        with index_lock:
            if not file_path.exists():
                raise HTTPException(status_code=404, detail="Document not found")
            file_path.unlink()
            vectorstore_service.delete_document(file_path.name)
        return {"message": "Document deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stats")
def get_statistics():
    """Get system statistics"""
    return {
        "statistics": {**stats, "total_documents": len(pdf_files())},
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/security/logs")
def get_security_logs(limit: int = Query(50, ge=1)):
    """Get the most recent security logs, newest first"""
    try:
        if not LOG_FILE.exists():
            return {"logs": [], "count": 0}

        with open(LOG_FILE) as f:
            logs = [json.loads(line) for line in deque(f, maxlen=limit)][::-1]
        return {"logs": logs, "count": len(logs)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "rag_agent": "operational",
            "vector_store": "operational",
            "embedding_model": vectorstore_service.embedding_model,
            "security": "operational"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

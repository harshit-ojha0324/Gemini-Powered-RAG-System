from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from collections import deque
import shutil
from datetime import datetime
import json
from pathlib import Path
from dotenv import load_dotenv

# Load backend/.env before the services below read their settings.
load_dotenv()

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
# One VectorStoreService for the whole process: the agent must query the same
# instance the upload path writes to, or /api/reset-embeddings resets a store
# nobody reads while queries keep serving vectors from a second, stale one.
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

# Request/Response Models
class QueryRequest(BaseModel):
    question: str
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
async def upload_document(file: UploadFile = File(...)):
    """Upload and process a PDF document"""
    try:
        if not file.filename or not file.filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are allowed")

        # Never write to a client-controlled path.
        resolved = resolve_document_path(file.filename)
        safe_name = resolved.name
        with open(resolved, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        documents = document_processor.process_pdf(str(resolved))
        vectorstore_service.add_documents(documents, safe_name)

        return {
            "message": "Document uploaded and processed successfully",
            "filename": safe_name,
            "chunks": len(documents),
            "status": "success"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing document: {str(e)}")

@app.post("/api/query", response_model=QueryResponse)
async def query_documents(request: QueryRequest):
    """Query documents with security checks"""
    try:
        stats["total_queries"] += 1
        security_warnings = []
        
        validation_result = input_validator.validate(request.question)
        if not validation_result["is_valid"]:
            security_warnings.extend(validation_result["warnings"])
            log_security_incident(request.question, validation_result["warnings"], False)
        
        # Redact detected PII so it reaches neither the audit log nor the LLM.
        safe_question, pii_types = pii_detector.redact(request.question)
        if pii_types:
            security_warnings.append(f"PII detected and redacted: {', '.join(pii_types)}")
            log_security_incident(safe_question, ["PII_DETECTED"], True)
        
        if any(w.startswith("INJECTION") for w in security_warnings):
            raise HTTPException(status_code=400, detail="Query blocked due to security concerns")
        
        result = rag_agent.query(safe_question, request.conversation_history)
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
async def list_documents():
    """List all uploaded documents"""
    try:
        documents = [
            {
                "filename": f.name,
                "size": f.stat().st_size,
                "uploaded_at": datetime.fromtimestamp(f.stat().st_mtime).isoformat()
            }
            for f in DOCUMENTS_DIR.glob("*.pdf")
        ]
        return {"documents": documents, "count": len(documents)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/documents/{filename}")
async def delete_document(filename: str):
    """Delete a document"""
    try:
        file_path = resolve_document_path(filename)
        if file_path.exists():
            file_path.unlink()
            vectorstore_service.delete_document(file_path.name)
            return {"message": "Document deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="Document not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stats")
async def get_statistics():
    """Get system statistics"""
    return {
        "statistics": {**stats, "total_documents": len(list(DOCUMENTS_DIR.glob("*.pdf")))},
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/security/logs")
async def get_security_logs(limit: int = Query(50, ge=1)):
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
    embeddings = vectorstore_service.embeddings
    degraded = embeddings.is_degraded
    return {
        "status": "degraded" if degraded else "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "rag_agent": "operational",
            # A live embedding fallback silently changes what retrieval returns,
            # so it has to be visible rather than only in the server logs.
            "vector_store": "degraded" if degraded else "operational",
            "embedding_mode": embeddings.mode,
            "security": "operational"
        }
    }

@app.post("/api/reset-embeddings")
async def reset_embeddings():
    """Reset to try Gemini embeddings again after quota reset"""
    vectorstore_service.embeddings.reset_to_primary()
    return {"message": "Reset to Gemini embeddings", "status": "success"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

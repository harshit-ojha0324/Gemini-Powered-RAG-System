import os
from typing import List, Optional
from dotenv import load_dotenv

# Apply telemetry compatibility shim before importing chromadb
from services.telemetry_shim import enable_telemetry_with_shim, disable_telemetry

# Attempt to enable telemetry with shim; falls back to disabled if shim fails
teleemetry_enabled = enable_telemetry_with_shim()

from langchain_community.vectorstores import Chroma
from langchain.schema import Document
from services.embedding_fallback import FallbackEmbeddings

load_dotenv()

class VectorStoreService:
    def __init__(self):
        # Use fallback embeddings instead of direct Gemini
        self.embeddings = FallbackEmbeddings()
        
        self.persist_directory: str = os.getenv("CHROMA_PERSIST_DIRECTORY", "./data/vectorstore")
        
        self.vectorstore = Chroma(
            persist_directory=self.persist_directory,
            embedding_function=self.embeddings,
            collection_name="documents"
        )
    
    def add_documents(self, documents: List[Document], source: Optional[str] = None) -> None:
        """Add documents to the vector store"""
        try:
            if source:
                for doc in documents:
                    doc.metadata["source"] = source
            
            self.vectorstore.add_documents(documents)
            self.vectorstore.persist()
        
        except Exception as e:
            raise Exception(f"Error adding documents: {str(e)}")
    
    def get_retriever(self, k: int = 4):
        """Get a retriever for querying"""
        return self.vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={"k": k}
        )
    
    def similarity_search(self, query: str, k: int = 4) -> List[Document]:
        """Search for similar documents"""
        return self.vectorstore.similarity_search(query, k=k)
    
    def delete_document(self, source: str):
        """Delete documents by source"""
        try:
            results = self.vectorstore.get(where={"source": source})
            if results and results['ids']:
                self.vectorstore.delete(ids=results['ids'])
                self.vectorstore.persist()
        except Exception as e:
            raise Exception(f"Error deleting documents: {str(e)}")
    
    def clear_all(self):
        """Clear all documents from vectorstore"""
        self.vectorstore.delete_collection()
        self.vectorstore = Chroma(
            persist_directory=self.persist_directory,
            embedding_function=self.embeddings,
            collection_name="documents"
        )
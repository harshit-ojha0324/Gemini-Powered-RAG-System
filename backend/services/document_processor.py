from pypdf import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from typing import List
import os

class DocumentProcessor:
    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
    
    def process_pdf(self, file_path: str) -> List[Document]:
        """Process a PDF file and return document chunks"""
        try:
            reader = PdfReader(file_path)
            documents = []
            
            for page_num, page in enumerate(reader.pages):
                text = page.extract_text()
                
                if text and text.strip():
                    doc = Document(
                        page_content=text,
                        metadata={
                            "source": os.path.basename(file_path),
                            "page": page_num + 1,
                            "total_pages": len(reader.pages)
                        }
                    )
                    documents.append(doc)
            
            chunks = self.text_splitter.split_documents(documents)
            return chunks
        
        except Exception as e:
            raise Exception(f"Error processing PDF: {str(e)}")
    
    def extract_metadata(self, file_path: str) -> dict:
        """Extract metadata from PDF"""
        try:
            reader = PdfReader(file_path)
            metadata = reader.metadata
            
            return {
                "title": metadata.get("/Title", "Unknown"),
                "author": metadata.get("/Author", "Unknown"),
                "pages": len(reader.pages),
                "file_size": os.path.getsize(file_path)
            }
        except Exception as e:
            return {"error": str(e)}
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate
from typing import List, Dict, Optional
import os
from dotenv import load_dotenv
from google.api_core.exceptions import ResourceExhausted
from tenacity import retry, stop_after_attempt, retry_if_exception_type
import google.api_core.exceptions as _gexc
import langchain_google_genai.chat_models as _gcm

# Patch langchain-google-genai 0.0.6 which hardcodes 10 retries on ResourceExhausted.
# We only retry transient ServiceUnavailable errors, not quota errors.
def _patched_retry_decorator():
    return retry(
        reraise=True,
        stop=stop_after_attempt(1),
        retry=retry_if_exception_type(_gexc.ServiceUnavailable),
    )
_gcm._create_retry_decorator = _patched_retry_decorator

from services.vectorstore import VectorStoreService
from agents.prompt_templates import RAG_PROMPT_TEMPLATE, CONDENSE_QUESTION_TEMPLATE

load_dotenv()

class RAGAgent:
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(  # type: ignore[call-arg]
            model="gemini-2.0-flash",
            temperature=0.3,
            google_api_key=os.getenv("GEMINI_API_KEY")
        )
        self.vectorstore_service = VectorStoreService()
        self.retriever = self.vectorstore_service.get_retriever()
        
        self.qa_prompt = PromptTemplate(
            template=RAG_PROMPT_TEMPLATE,
            input_variables=["context", "question"]
        )
        
        self.condense_prompt = PromptTemplate(
            template=CONDENSE_QUESTION_TEMPLATE,
            input_variables=["chat_history", "question"]
        )
        
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
            output_key="answer"
        )
        
        self.chain = ConversationalRetrievalChain.from_llm(
            llm=self.llm,
            retriever=self.retriever,
            memory=self.memory,
            combine_docs_chain_kwargs={"prompt": self.qa_prompt},
            condense_question_prompt=self.condense_prompt,
            return_source_documents=True,
            verbose=False
        )
    
    def query(self, question: str, conversation_history: Optional[List[Dict]] = None) -> Dict:
        """Process a query and return answer with sources"""
        try:
            self.memory.clear()
            if conversation_history:
                for msg in conversation_history:
                    if msg["role"] == "user":
                        self.memory.chat_memory.add_user_message(msg["content"])
                    elif msg["role"] == "assistant":
                        self.memory.chat_memory.add_ai_message(msg["content"])
            
            result = self.chain({"question": question})
            
            sources = []
            for doc in result.get("source_documents", []):
                sources.append({
                    "content": doc.page_content[:200] + "...",
                    "metadata": doc.metadata,
                    "page": doc.metadata.get("page", "N/A"),
                    "source": doc.metadata.get("source", "Unknown")
                })
            
            return {
                "answer": result["answer"],
                "sources": sources,
                "question": question
            }
        
        except ResourceExhausted:
            return {
                "answer": "Gemini API quota exceeded. The free tier daily limit has been reached. Please wait until midnight (Pacific Time) for the quota to reset, or use a new API key.",
                "sources": [],
                "question": question
            }
        except Exception as e:
            return {
                "answer": f"I apologize, but I encountered an error: {str(e)}",
                "sources": [],
                "question": question
            }
    
    def clear_memory(self):
        """Clear conversation memory"""
        self.memory.clear()
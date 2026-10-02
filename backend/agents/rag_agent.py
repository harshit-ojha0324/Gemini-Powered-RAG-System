from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains import ConversationalRetrievalChain
from langchain.prompts import PromptTemplate
from langchain.schema import AIMessage, HumanMessage
from typing import List, Dict, Optional
import logging
import os
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

logger = logging.getLogger(__name__)

# Google's alias for its newest Flash model. Fixed IDs get retired (gemini-2.0-flash
# was shut down on June 1, 2026), which turned every answer into a 404.
CHAT_MODEL = "gemini-flash-latest"

class RAGAgent:
    def __init__(self, vectorstore_service: Optional[VectorStoreService] = None):
        self.llm = ChatGoogleGenerativeAI(  # type: ignore[call-arg]
            model=CHAT_MODEL,
            temperature=0.3,
            google_api_key=os.getenv("GEMINI_API_KEY")
        )
        # Injected by the app so the agent reads the same store the upload path
        # writes to. Constructing one here is a fallback for standalone use.
        self.vectorstore_service = vectorstore_service or VectorStoreService()
        self.retriever = self.vectorstore_service.get_retriever()
        
        self.qa_prompt = PromptTemplate(
            template=RAG_PROMPT_TEMPLATE,
            input_variables=["context", "question"]
        )
        
        self.condense_prompt = PromptTemplate(
            template=CONDENSE_QUESTION_TEMPLATE,
            input_variables=["chat_history", "question"]
        )

        # No memory object: the client sends the history with each request, so
        # the chain stays stateless and one agent can serve every caller.
        self.chain = ConversationalRetrievalChain.from_llm(
            llm=self.llm,
            retriever=self.retriever,
            combine_docs_chain_kwargs={"prompt": self.qa_prompt},
            condense_question_prompt=self.condense_prompt,
            return_source_documents=True,
            verbose=False
        )
    
    def query(self, question: str, conversation_history: Optional[List[Dict]] = None) -> Dict:
        """Process a query and return answer with sources"""
        try:
            chat_history = [
                HumanMessage(content=msg["content"]) if msg["role"] == "user" else AIMessage(content=msg["content"])
                for msg in conversation_history or []
                if msg["role"] in ("user", "assistant")
            ]
            result = self.chain({"question": question, "chat_history": chat_history})
            
            sources = []
            for doc in result.get("source_documents", []):
                sources.append({
                    "content": doc.page_content[:200] + "...",
                    "page": doc.metadata.get("page", "N/A"),
                    "source": doc.metadata.get("source", "Unknown")
                })
            
            return {
                "answer": result["answer"],
                "sources": sources
            }
        
        except ResourceExhausted as e:
            # Google's message names the quota that ran out (per minute or per day).
            logger.warning(f"Gemini quota exhausted: {e}")
            return {
                "answer": "Gemini's rate limit was hit. Wait a minute and try again; if it keeps happening, the free tier's daily quota is used up and resets at midnight Pacific time.",
                "sources": []
            }
        except Exception as e:
            # The client only sees the message; the traceback belongs in the server log.
            logger.exception("Query failed")
            return {
                "answer": f"I apologize, but I encountered an error: {str(e)}",
                "sources": []
            }
import google.generativeai as genai
from typing import List, Dict
import os
from dotenv import load_dotenv

load_dotenv()

class LLMService:
    def __init__(self):
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        self.model = genai.GenerativeModel("models/gemini-2.0-flash-exp")
    
    def generate_response(self, messages: List[Dict[str, str]], 
                         temperature: float = 0.7) -> str:
        """Generate a response using Gemini API"""
        try:
            prompt_parts = []
            for msg in messages:
                role = "user" if msg["role"] == "user" else "model"
                prompt_parts.append(f"{role}: {msg['content']}")
            
            prompt = "\n".join(prompt_parts)
            
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=temperature
                )
            )
            return response.text
        except Exception as e:
            raise Exception(f"Error generating response: {str(e)}")
    
    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text"""
        try:
            result = genai.embed_content(
                model="models/embedding-001",
                content=text,
                task_type="retrieval_document"
            )
            return result['embedding']
        except Exception as e:
            raise Exception(f"Error generating embedding: {str(e)}")
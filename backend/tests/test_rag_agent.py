import pytest
from agents.rag_agent import RAGAgent

@pytest.fixture
def rag_agent():
    return RAGAgent()

def test_rag_agent_initialization(rag_agent):
    """Test RAG agent initializes correctly"""
    assert rag_agent.llm is not None
    assert rag_agent.retriever is not None
    assert rag_agent.chain is not None

def test_query_structure(rag_agent):
    """Test query returns correct structure"""
    result = rag_agent.query("What is AI?")
    assert "answer" in result
    assert "sources" in result
    assert isinstance(result["sources"], list)
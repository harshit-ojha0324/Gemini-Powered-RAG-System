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

def test_history_is_per_request(rag_agent):
    """Each query sees only the history it was sent, never a previous caller's."""
    seen = []
    rag_agent.chain = lambda inputs: seen.append(inputs) or {"answer": "a", "source_documents": []}
    rag_agent.query("q2", [{"role": "user", "content": "q1"}, {"role": "assistant", "content": "a1"}])
    rag_agent.query("q3")
    assert [m.content for m in seen[0]["chat_history"]] == ["q1", "a1"]
    assert seen[1]["chat_history"] == []
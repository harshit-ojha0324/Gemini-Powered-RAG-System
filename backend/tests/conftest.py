import pytest
import os
from pathlib import Path

@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Setup test environment"""
    Path("./data/documents").mkdir(parents=True, exist_ok=True)
    Path("./data/logs").mkdir(parents=True, exist_ok=True)
    Path("./data/vectorstore").mkdir(parents=True, exist_ok=True)
    
    os.environ["GEMINI_API_KEY"] = os.getenv("GEMINI_API_KEY", "test-key")
    
    yield
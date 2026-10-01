import os
import tempfile

# Runs before any test module imports app, so every ./data path the app uses
# (uploads, vector store, security log) lands in a throwaway directory instead
# of backend/data, where a developer's real documents live.
os.chdir(tempfile.mkdtemp(prefix="rag-tests-"))

# The Gemini clients only need a key to exist; the tests never call Gemini.
os.environ.setdefault("GEMINI_API_KEY", "test-key")

import os
from pathlib import Path

# Paths
PROJ_ROOT = Path(__file__).parent
DATA_DIR = PROJ_ROOT / "data"
DEFAULT_REPO = DATA_DIR / "sample_repo"

# Settings
ALLOWED_EXT = {".py", ".md", ".txt", ".html", ".js", ".css", ".java", ".cpp"}
CHUNK_SIZE = 50  # lines per chunk
TOP_K = 7

# Models
EMBED_MODEL = "models/text-embedding-004"  # Gemini's Cloud Embeddings
GEMINI_MODEL = "gemini-2.0-flash"
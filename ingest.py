import os
import shutil
import chromadb
import google.generativeai as genai
from chromadb import Documents, EmbeddingFunction, Embeddings
from pathlib import Path
from config import EMBED_MODEL, CHUNK_SIZE
from utils import read_file, chunk_text, chunk_python_ast, is_allowed

# Add folders to ignore to prevent indexing libraries/env
IGNORED_DIRS = {"venv", ".venv", "env", ".env", ".git", "__pycache__", "node_modules", "site-packages", "build", "dist"}

class GeminiEmbeddingFunction(EmbeddingFunction):
    def __init__(self, api_key: str):
        self.api_key = api_key

    def __call__(self, input: Documents) -> Embeddings:
        genai.configure(api_key=self.api_key)
        # Use task_type="retrieval_document" for indexing
        result = genai.embed_content(
            model=EMBED_MODEL,
            content=input,
            task_type="retrieval_document"
        )
        return result['embedding']

def ingest_repo(repo_path: Path, db_path: Path, api_key: str):
    """Ingests repo into a specific DB path using Gemini Embeddings."""
    
    # 1. Setup Clean DB
    # Ensure DB folder is deleted to prevent collection existence error ---
    if db_path.exists():
        shutil.rmtree(db_path)
    db_path.mkdir(parents=True, exist_ok=True)

    client = chromadb.PersistentClient(path=str(db_path))
    embedding_fn = GeminiEmbeddingFunction(api_key)
    
    collection = client.create_collection(
        name="code_chunks",
        embedding_function=embedding_fn
    )

    # 2. Scan & Chunk
    docs, metas, ids = [], [], []
    counter = 0
    
    print(f"Scanning {repo_path}...")
    
    # Change '_' to 'dirs' so we can modify it
    for root, dirs, files in os.walk(repo_path):
        # Modify 'dirs' in-place to stop recursion into ignored folders
        dirs[:] = [d for d in dirs if d not in IGNORED_DIRS]
        
        for f in files:
            path = Path(root) / f
            if not is_allowed(path): continue

            text = read_file(path)
            if not text: continue

            if path.suffix == ".py":
                chunks = chunk_python_ast(text)
            else:
                chunks = chunk_text(text, CHUNK_SIZE)

            for c in chunks:
                docs.append(c["content"])
                metas.append({
                    "file_path": str(path.relative_to(repo_path)),
                    "start_line": c["start"],
                    "end_line": c["end"],
                    "type": c.get("type", "text"),
                    "name": c.get("name", "")
                })
                ids.append(f"id_{counter}")
                counter += 1

    # 3. Batch Insert
    if not docs:
        print("No valid files found.")
        return

    print(f"Indexing {len(docs)} chunks...")
    BATCH_SIZE = 100
    for i in range(0, len(docs), BATCH_SIZE):
        end = i + BATCH_SIZE
        collection.add(
            documents=docs[i:end],
            metadatas=metas[i:end],
            ids=ids[i:end]
        )
    print("Ingestion complete.")
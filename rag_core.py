import google.generativeai as genai
import chromadb
from config import GEMINI_MODEL, TOP_K
from ingest import GeminiEmbeddingFunction

def query_repo(question: str, db_path: str, api_key: str):
    """Queries Chroma DB using Gemini for answer generation."""
    
    # 1. Retrieve
    client = chromadb.PersistentClient(path=str(db_path))
    embedding_fn = GeminiEmbeddingFunction(api_key)
    collection = client.get_collection("code_chunks", embedding_function=embedding_fn)

    results = collection.query(
        query_texts=[question],
        n_results=TOP_K
    )
    
    if not results['documents'] or not results['documents'][0]:
        return "No relevant code found.", []

    # 2. Build Context
    context_parts = []
    retrieved_docs = [] 
    
    docs = results['documents'][0]
    metas = results['metadatas'][0]
    
    for i, doc_text in enumerate(docs):
        meta = metas[i]
        loc = f"{meta['file_path']} (L{meta['start_line']}-{meta['end_line']})"
        if meta.get('name'):
            loc += f" [{meta['type']}: {meta['name']}]"
            
        context_parts.append(f"--- SOURCE START: {loc} ---\n{doc_text}\n--- SOURCE END ---")
        
        retrieved_docs.append({
            "page_content": doc_text,
            "metadata": meta
        })

    # 3. Generate Answer (High-Performance Prompt)
    context_str = "\n\n".join(context_parts)
    
    prompt = f"""
    You are a Senior Principal Engineer analyzing a codebase.
    
    **INSTRUCTIONS:**
    1. Answer the question based **ONLY** on the provided context.
    2. Be technically precise. Mention specific **file names**, **function names**, **variables**, and **libraries**.
    3. If the answer involves a process (like ingestion), step through the logic flow explicitly.
    4. If the context contains specific constants (e.g., model names, numbers), quote them exactly.
    5. Do not hallucinate. If the code is not in the context, say "I cannot find that in the provided context."

    **CONTEXT:**
    {context_str}
    
    **QUESTION:**
    {question}
    """
    
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(GEMINI_MODEL)
    
    try:
        response = model.generate_content(prompt)
        return response.text, retrieved_docs
    except Exception as e:
        return f"Error generating answer: {e}", []

def explain_file(file_path: str, db_path: str, api_key: str):
    """Fetches all chunks for a specific file and explains them."""
    client = chromadb.PersistentClient(path=str(db_path))
    embedding_fn = GeminiEmbeddingFunction(api_key)
    collection = client.get_collection("code_chunks", embedding_function=embedding_fn)
    
    results = collection.get(where={"file_path": file_path})
    
    if not results['documents']:
        return "File not found in index.", []

    # Sort chunks by line number
    combined = list(zip(results['documents'], results['metadatas']))
    combined.sort(key=lambda x: x[1]['start_line'])
    
    full_code = "\n".join([c[0] for c in combined])
    
    prompt = f"Explain this file's logic and architecture:\n\n{full_code}"
    
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(GEMINI_MODEL)
    
    try:
        response = model.generate_content(prompt)
        return response.text, [] 
    except Exception as e:
        return f"Error: {e}", []
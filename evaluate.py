import os
import json
import time
import shutil
import tempfile
import gc
import google.generativeai as genai
from pathlib import Path
from rag_core import query_repo
from ingest import ingest_repo
from config import GEMINI_MODEL, DEFAULT_REPO

# Test Questions
TEST_SET = [
    {"q": "How does ingestion work?", "expected": ["ingest_repo", "Chroma"]},
    {"q": "Where is file reading?", "expected": ["read_file", "utils.py"]},
    {"q": "What are allowed extensions?", "expected": ["config.py", ".py"]},
    {"q": "How are chunks created?", "expected": ["chunk_text", "chunk_python_ast"]},
    {"q": "What embedding model is used?", "expected": ["text-embedding-004", "Gemini"]},
    {"q": "Explain the RAG query function.", "expected": ["query_repo", "collection.query"]},
    {"q": "Does it support decorators?", "expected": ["decorator_list", "ast"]},
    {"q": "How are files processed?", "expected": ["read_file", "utf-8"]},
    {"q": "What vector database is used?", "expected": ["Chroma", "PersistentClient"]},
    {"q": "How does semantic chunking work?", "expected": ["AST", "FunctionDef"]}
]

LATENCY_THRESHOLD = 3.0  # seconds

def evaluate_answer(q, ans, expected, api_key):
    """Uses Gemini to grade the answer 1-5."""
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(GEMINI_MODEL)
    
    prompt = f"""
    You are a strict code reviewer. Rate this answer from 1 to 5.
    
    Question: {q}
    System Answer: {ans}
    Expected Keywords/Concepts: {expected}
    
    Criteria:
    1: Wrong or irrelevant.
    3: Partially correct but missing details.
    5: Perfect, accurate, and mentions expected concepts.
    
    OUTPUT ONLY THE NUMBER (e.g., 5). Do not write words.
    """
    try:
        response = model.generate_content(prompt)
        text = response.text.strip()
        # Clean potential markdown like **5** or "5."
        clean_score = ''.join(filter(str.isdigit, text))
        return int(clean_score)
    except Exception as e:
        print(f"  ⚠️ Eval Error: {e}")
        return 1

def run():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("❌ Error: GEMINI_API_KEY not found in environment.")
        return

    # 1. Setup Temporary Test DB
    temp_dir = Path(tempfile.mkdtemp())
    test_db_path = temp_dir / "eval_db"
    
    print(f"🧪 Starting Evaluation using model: {GEMINI_MODEL}")
    print(f"📂 Indexing {DEFAULT_REPO} into temp DB...")
    
    try:
        target_repo = DEFAULT_REPO if DEFAULT_REPO.exists() else Path(".")
        
        # Ingest
        ingest_repo(target_repo, test_db_path, api_key)
        
        results = []
        print(f"\n📝 Grading {len(TEST_SET)} questions...\n")

        for i, t in enumerate(TEST_SET, 1):
            start = time.time()
            
            # Query
            ans, srcs = query_repo(t["q"], test_db_path, api_key)
            
            lat = time.time() - start
            score = evaluate_answer(t["q"], ans, t["expected"], api_key)
            status = "✅" if score >= 4 else "⚠️"
            
            print(f"{i}. {t['q'][:40]:40} | Score: {score}/5 | Time: {lat:.2f}s {status}")
            
            results.append({
                "question": t["q"],
                "score": score,
                "latency": lat,
                "sources_count": len(srcs)
            })
            
            # Brief sleep to avoid rate limits
            time.sleep(6)

        # Summary
        if results:
            avg_score = sum(r["score"] for r in results) / len(results)
            avg_lat = sum(r["latency"] for r in results) / len(results)
            
            print(f"\n{'='*50}")
            print(f"📊 FINAL REPORT")
            print(f"Avg Score:   {avg_score:.2f} / 5.0")
            print(f"Avg Latency: {avg_lat:.2f}s")
            print(f"{'='*50}")
            
            with open("evaluation_report.json", "w") as f:
                json.dump(results, f, indent=2)
            print("✅ Saved detailed report to evaluation_report.json")

    except Exception as e:
        print(f"\n❌ Critical Failure: {e}")

    finally:
        # Cleanup temp DB
        print("🧹 Cleaning up...")
        gc.collect() # Force garbage collection to release file locks
        try:
            shutil.rmtree(temp_dir, ignore_errors=True)
        except Exception as e:
            print(f"Warning: Could not fully delete temp dir: {e}")

if __name__ == "__main__":
    run()
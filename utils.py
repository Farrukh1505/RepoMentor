import ast
from pathlib import Path
from bs4 import BeautifulSoup
from config import ALLOWED_EXT

def is_allowed(path: Path) -> bool:
    return path.suffix in ALLOWED_EXT and not any(p.startswith(".") for p in path.parts)

def read_file(path: Path) -> str:
    try:
        content = path.read_text(encoding="utf-8", errors="ignore")
        if path.suffix == ".html":
            soup = BeautifulSoup(content, "html.parser")
            return soup.get_text(separator="\n")
        return content
    except Exception:
        return ""

def chunk_text(text: str, max_lines: int) -> list:
    lines = text.splitlines()
    chunks = []
    for i in range(0, len(lines), max_lines):
        chunk_str = "\n".join(lines[i : i + max_lines])
        chunks.append({
            "content": chunk_str,
            "start": i + 1,
            "end": min(i + max_lines, len(lines)),
            "type": "text"
        })
    return chunks

def chunk_python_ast(text: str) -> list:
    chunks = []
    lines = text.splitlines()
    
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return chunk_text(text, 50)

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if not hasattr(node, 'end_lineno'): 
                continue
                
            start, end = node.lineno, node.end_lineno
            chunk_content = "\n".join(lines[start-1 : end])
            
            if hasattr(node, 'decorator_list') and node.decorator_list:
                dec_start = node.decorator_list[0].lineno
                chunk_content = "\n".join(lines[dec_start-1 : end])
                start = dec_start

            chunks.append({
                "content": chunk_content,
                "start": start,
                "end": end,
                "type": "code_block",
                "name": node.name
            })
            
    if not chunks:
        return chunk_text(text, 50)
        
    return chunks
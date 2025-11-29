RepoMentor

RepoMentor is a cloud-ready RAG (Retrieval-Augmented Generation) engine for codebase analysis. It allows developers to upload repository archives (.zip) and perform architectural querying and logic explanation using Google's Gemini API.

Unlike standard text search, RepoMentor utilizes AST (Abstract Syntax Tree) parsing for Python. This ensures vector embeddings represent complete logical units (functions and classes) rather than arbitrary text chunks, significantly improving retrieval precision.

Core Features

Zip Upload Interface: Analysis runs entirely via the web UI. Simply upload a zipped repository to start indexing.

AST-Aware Indexing: Parses Python source code into semantic blocks (FunctionDef, ClassDef) to preserve logical context.

Strict Source Grounding: All responses are cited with precise file paths and line number ranges (e.g., src/utils.py L45-L90).

Gemini Powered: Leverages Google's Gemini 1.5 Flash for high-speed, cost-effective code reasoning.

Dual Operation Modes:

Global Query: Repository-wide architectural search.

File Inspection: Deep-dive explanation of specific modules.

Technical Architecture

Inference Engine: Google Gemini 1.5 Flash

Vector Store: ChromaDB (Ephemeral/Session-based)

Embeddings: all-MiniLM-L6-v2 (HuggingFace)

Orchestration: LangChain Community

Interface: Streamlit

Installation

Prerequisites

Python 3.10+

Google Gemini API Key

Setup

Clone the repository

git clone [https://github.com/yourusername/repomentor.git](https://github.com/yourusername/repomentor.git)
cd repomentor


Install dependencies

pip install -r requirements.txt


Configure Environment (Optional)
You can export your API key globally, or enter it securely in the UI sidebar each time.

export GEMINI_API_KEY="your_api_key_here"


Usage

Start the application using the cloud-optimized entry point:

streamlit run app.py


Once running:

Enter your Gemini API Key in the sidebar (if not set in env).

Upload a .zip file of your target repository.

Click Index Repository.

Select "General Q&A" or "Explain File" to begin.

Docker Deployment

RepoMentor includes a Dockerfile for isolated execution, pre-configured for the cloud interface.

# Build
docker build -t repomentor .

# Run (Access at http://localhost:8501)
docker run -p 8501:8501 -e GEMINI_API_KEY="your_key" repomentor


Configuration

Indexing and model parameters can be adjusted in config.py:

Parameter

Default

Description

ALLOWED_EXT

.py, .js, .html...

File extensions included in the index.

CHUNK_SIZE

50

Line count for non-AST chunking (text/html).

GEMINI_MODEL

gemini-1.5-flash

LLM version. Switch to pro for complex tasks.

Project Structure

repomentor/
├── app.py        # Main Application (UI + Logic)
├── ingest.py           # Vectorization and indexing pipeline
├── rag_core.py         # RAG logic and Gemini interaction
├── utils.py            # AST parsing and file I/O utilities
├── config.py           # Application configuration
├── Dockerfile          # Container definition
└── requirements.txt    # Python dependencies

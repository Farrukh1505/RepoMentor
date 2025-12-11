# 🧠 **RepoMentor: Codebase RAG System**

A robust Retrieval-Augmented Generation (RAG) system designed to ingest, analyze, and explain complex codebases using **Google Gemini** and **ChromaDB**.

## ✨ Features
* **Smart Ingestion:** Uses Python AST to understand functions, classes, and global variables.
* **Robust Parsing:** Automatically handles binary files and encoding errors.
* **Self-Correction:** Handles API Rate Limits (429 errors) with automatic retries.
* **Evaluation Suite:** Includes an "LLM-as-a-Judge" script to grade its own accuracy.

--------------------------------------------------------------------------------------



## **🚀 Setup & Installation**

**1. Clone the Repository**

git clone [https://github.com/YOUR_USERNAME/RepoMentor.git](https://github.com/YOUR_USERNAME/RepoMentor.git)
cd RepoMentor

**2. Create a Virtual Environment**

It is recommended to use a virtual environment to keep your dependencies clean.

macOS / Linux: 
python3 -m venv venv
source venv/bin/activate

Windows: 
python -m venv venv
venv\Scripts\activate


**3. Install Dependencies**

Since you are setting this up for others (or yourself later), you need to list the libraries used. Create a file named requirements.txt and paste this:

google-generativeai
chromadb
beautifulsoup4
python-dotenv

pip install -r requirements.txt


## **🔑 Configuration**

You need a Google Gemini API Key to run this project.

### 📌 For the Streamlit Web App (`app.py`):
**Primary Option (Recommended): Streamlit Secrets**
1.  Create a folder `.streamlit` in your project root.
2.  Inside, create a file named `secrets.toml`.
3.  Add your API key using the standard name:
    ```toml
    GEMINI_API_KEY = "your_api_key_here"
    ```
    The web app will automatically load the key from here.

### 📌 For the Evaluation Script (`evaluate.py`):
**Option 1: Environment Variable**

macOS / Linux: 
export GEMINI_API_KEY="your_api_key_here"

Windows: (Command Prompt)
set GEMINI_API_KEY=your_api_key_here

Option 2: .env file (For local testing) Create a file named .env in the root folder and add:

GEMINI_API_KEY=your_api_key_here



## **📊 Running the Evaluation**

We have a built-in testing suite that grades the system's accuracy on a scale of 1-5.
Run the evaluation script:

python evaluate.py

What happens?
The system ingests its own source code into a temporary vector database.
It asks itself 10 technical questions (e.g., "How does ingestion work?").
A "Judge" model grades the answers.
It generates a final report evaluation_report.json and prints the score.

Passing Criteria:

Score: > 3.5 / 5.0

Latency: < 3 seconds per query


## **📂 Project Structure**

ingest.py: Scans files, chunks code using AST, and saves to ChromaDB.

rag_core.py: Handles retrieval and answer generation using Gemini.

evaluate.py: The test suite. Runs queries and grades them.

config.py: Configuration settings (Chunk size, Model names).

utils.py: Helper functions for safe file reading and AST parsing.



## **Push to GitHub**

Now that you have documentation, save it to the cloud:

git add README.md requirements.txt

git commit -m "Add documentation and requirements"

git push

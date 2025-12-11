import sys
import os
import subprocess

# Cloud fix for Linux only
if sys.platform.startswith('linux'):
    __import__('pysqlite3')
    sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

import zipfile
import shutil
import tempfile
import streamlit as st
import uuid
from pathlib import Path
from ingest import ingest_repo
from rag_core import query_repo, explain_file

st.set_page_config(page_title="RepoMentor", layout="wide")
st.title("RepoMentor")

# 1. Initialize Session
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

# Define paths specific to this user session
BASE_TEMP = Path(tempfile.gettempdir()) / "repomentor"
SESSION_DIR = BASE_TEMP / st.session_state.session_id
REPO_DIR = SESSION_DIR / "repo"
DB_DIR = SESSION_DIR / "db"

GEMINI_KEY_NAME = "GEMINI_API_KEY"

if "api_key" not in st.session_state:
    if GEMINI_KEY_NAME in st.secrets:
        st.session_state.api_key = st.secrets[GEMINI_KEY_NAME]
    else:
        # Set to empty string if not found in secrets (will trigger error in sidebar)
        st.session_state.api_key = ""

if "repo_ready" not in st.session_state:
    st.session_state.repo_ready = False

# 2. Sidebar Setup
with st.sidebar:
    st.header("Setup")
    if not st.session_state.api_key:
        st.error(f"API Key required.")
        st.caption(f"Please configure '{GEMINI_KEY_NAME}' in your Streamlit secrets.")
        st.stop()
    else:
        st.success("API Key loaded.")
    
    # --- NEW: Source Selection ---
    data_source = st.radio("Data Source", ["Upload Zip", "GitHub URL"])
    
    if data_source == "Upload Zip":
        uploaded = st.file_uploader("Upload Repo (.zip)", type="zip")
        repo_url = None
    else:
        uploaded = None
        repo_url = st.text_input("GitHub Repo URL", placeholder="https://github.com/user/repo")
        st.caption("Note: Public repositories only.")

    if st.button("🚀 Start"):
        if not st.session_state.api_key:
            st.error("API Key required.")
        elif data_source == "Upload Zip file" and not uploaded:
            st.error("Please upload a zip file.")
        elif data_source == "GitHub URL" and not repo_url:
            st.error("Please enter a GitHub URL.")
        else:
            # Cleanup previous data
            if SESSION_DIR.exists(): shutil.rmtree(SESSION_DIR)
            REPO_DIR.mkdir(parents=True, exist_ok=True)
            
            try:
                with st.spinner("Preparing repository..."):
                    if data_source == "Upload Zip":
                        # ZIP LOGIC
                        zip_path = SESSION_DIR / "repo.zip"
                        zip_path.write_bytes(uploaded.getvalue())
                        with zipfile.ZipFile(zip_path, 'r') as z: 
                            z.extractall(REPO_DIR)
                    else:
                        result = subprocess.run(
                            ["git", "clone", "--depth", "1", repo_url, str(REPO_DIR)],
                            capture_output=True,
                            text=True
                        )
                        if result.returncode != 0:
                            raise Exception(f"Git clone failed: {result.stderr}")

                with st.spinner("Analyzing..."):
                    ingest_repo(REPO_DIR, DB_DIR, st.session_state.api_key)
                    st.session_state.repo_ready = True
                st.success("Ready!")
                
            except Exception as e:
                st.error(f"Error: {e}")

    mode = st.radio("Mode", ["General Q&A", "Explain File"])

if not st.session_state.repo_ready:
    st.info("👈 Connect a repository or upload a .zip file to start.")
    st.stop()

# 3. Main Interface
if mode == "General Q&A":
    q = st.text_area("Question:")
    if st.button("Ask"):
        with st.spinner("Thinking..."):
            ans, srcs = query_repo(q, DB_DIR, st.session_state.api_key)
        st.markdown(ans)
        if srcs:
            st.markdown("### Sources")
            for d in srcs:
                st.caption(f"📄 {d['metadata']['file_path']}")
                st.code(d['page_content'])

elif mode == "Explain File":
    files = []
    for r, _, fs in os.walk(REPO_DIR):
        for f in fs:
            # Filter out hidden git files
            if ".git" not in str(Path(r)) and not f.startswith("."):
                files.append(str(Path(r).relative_to(REPO_DIR) / f))
    
    sel = st.selectbox("File", files)
    if st.button("Explain"):
        with st.spinner("Analyzing..."):
            ans, _ = explain_file(sel, DB_DIR, st.session_state.api_key)
        st.markdown(ans)
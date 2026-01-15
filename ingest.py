from langchain_huggingface import HuggingFaceEmbeddings
from langchain.schema import Document
from langchain_community.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import JSONLoader
import subprocess
import sys
import os
import json

# --- PART 1: AUTO-INSTALLER ---


def install_package(package):
    try:
        __import__(package)
    except ImportError:
        print(f"[INFO] Installing {package}...")
        try:
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", package])
        except subprocess.CalledProcessError:
            print(
                f"[ERROR] Failed to install {package}. Please install manually.")


# Map import names to pip package names
required_packages = {
    "langchain_community": "langchain-community",
    "langchain_huggingface": "langchain-huggingface",
    "chromadb": "chromadb",
    "pysqlite3": "pysqlite3-binary",
    "sentence_transformers": "sentence-transformers"
}

print("[INFO] Checking dependencies...")
for import_name, pip_name in required_packages.items():
    install_package(import_name)

# --- PART 2: WINDOWS SQLITE FIX ---
# This prevents crashes on Windows systems
try:
    __import__('pysqlite3')
    sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
except ImportError:
    pass

# --- PART 3: INGESTION LOGIC ---
# Now it is safe to import these libraries

DATA_FOLDER = "scraped_data"
DB_PATH = "vectorstore"


def run_ingest():
    print(f"[INFO] Starting ingestion from folder: {DATA_FOLDER}")

    if not os.path.exists(DATA_FOLDER):
        print(
            f"[ERROR] Folder '{DATA_FOLDER}' not found. Please run scrape.py first.")
        return

    # 1. Load Data
    documents = []
    files = [f for f in os.listdir(DATA_FOLDER) if f.endswith(".json")]

    if not files:
        print("[ERROR] No .json files found in the data folder.")
        return

    print(f"[INFO] Found {len(files)} batch files to process.")

    for filename in files:
        filepath = os.path.join(DATA_FOLDER, filename)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for page in data:
                    # Create a Document object with metadata for citations
                    doc = Document(
                        page_content=page['content'],
                        metadata={"source": page['url'],
                                  "title": page['title']}
                    )
                    documents.append(doc)
        except Exception as e:
            print(f"[WARNING] Could not read file {filename}: {e}")

    print(f"[INFO] Successfully loaded {len(documents)} articles.")

    # 2. Chunk Data
    print("[INFO] Splitting text into chunks...")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        separators=["\n\n", "\n", ".", " ", ""]
    )
    chunks = text_splitter.split_documents(documents)
    print(f"[INFO] Created {len(chunks)} text chunks.")

    # 3. Create Vector DB
    print("[INFO] Generating embeddings and saving to ChromaDB...")
    print("[NOTE] This process may take several minutes. Please wait.")

    try:
        embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

        vector_db = Chroma.from_documents(
            documents=chunks,
            embedding=embeddings,
            persist_directory=DB_PATH
        )

        print(f"[SUCCESS] Vector database has been saved to '{DB_PATH}'.")
        print("[INFO] You are now ready to run the chatbot.")

    except Exception as e:
        print(f"[ERROR] Failed to create vector database: {e}")


if __name__ == "__main__":
    run_ingest()

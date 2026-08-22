"""
Liara Agentic Copilot — ingest.py
Downloads Liara docs from GitHub, parses MDX, chunks text, and indexes into Qdrant.
"""
import os
import re
import uuid
import shutil
import zipfile
import tempfile
import urllib.request
from typing import List, Dict

from dotenv import load_dotenv

# Load vector_store which handles Qdrant client and Embedding model
from vector_store import _get_client, _get_embed_model, COLLECTION_NAME, STORAGE_PATH, _init_collection

load_dotenv()

DOCS_REPO_ZIP_URL = "https://github.com/liara-cloud/docs/archive/refs/heads/main.zip"

def download_and_extract() -> str:
    """Downloads the docs repo zip and extracts it to a temp dir."""
    print("[1/5] Downloading Liara docs repository...")
    temp_dir = tempfile.mkdtemp()
    zip_path = os.path.join(temp_dir, "docs.zip")
    
    urllib.request.urlretrieve(DOCS_REPO_ZIP_URL, zip_path)
    
    print("[2/5] Extracting files...")
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(temp_dir)
        
    # The extracted folder is usually named "docs-main"
    extract_dir = os.path.join(temp_dir, "docs-main")
    return extract_dir

def parse_mdx(filepath: str, base_dir: str) -> List[Dict]:
    """Reads MDX, strips frontmatter, extracts URL path, and returns chunks."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception:
        return []

    # Calculate relative URL path (e.g., src/pages/paas/nodejs/index.mdx -> /paas/nodejs/)
    rel_path = os.path.relpath(filepath, base_dir)
    # Liara docs usually store content in 'src/pages'
    if rel_path.startswith(os.path.join("src", "pages")):
        url_path = rel_path.replace(os.path.join("src", "pages"), "").replace(".mdx", "").replace(".md", "").replace("\\", "/")
        if url_path.endswith("/index"):
            url_path = url_path[:-6]
    else:
        url_path = rel_path.replace(".mdx", "").replace(".md", "").replace("\\", "/")

    full_url = f"https://docs.liara.ir{url_path}"

    # Extract title from frontmatter if exists
    title = ""
    frontmatter_match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
    if frontmatter_match:
        fm = frontmatter_match.group(1)
        title_match = re.search(r'title:\s*[\'"]?(.*?)[\'"]?\s*\n', fm)
        if title_match:
            title = title_match.group(1)
        # Strip frontmatter
        content = content[frontmatter_match.end():]

    # Clean JSX/import statements
    content = re.sub(r'^import .*$', '', content, flags=re.MULTILINE)
    content = re.sub(r'<Layout>.*?</Layout>', '', content, flags=re.DOTALL)
    content = content.strip()

    if not content:
        return []

    # Simple chunking by Markdown headings or paragraphs
    # We will do a simple character overlap chunking for robustness
    chunk_size = 1000
    overlap = 200
    chunks = []
    
    start = 0
    content_len = len(content)
    
    while start < content_len:
        end = start + chunk_size
        chunk_text = content[start:end]
        
        # Adjust end to nearest newline if not at end of text
        if end < content_len:
            last_newline = chunk_text.rfind('\n')
            if last_newline != -1 and last_newline > chunk_size // 2:
                end = start + last_newline
                chunk_text = content[start:end]

        chunks.append({
            "text": chunk_text.strip(),
            "url": full_url,
            "section": title
        })
        start = end - overlap

    return chunks

def process_directory(base_dir: str) -> List[Dict]:
    """Walks the directory and processes all .md/.mdx files."""
    print("[3/5] Parsing and chunking markdown files...")
    all_chunks = []
    
    for root, _, files in os.walk(base_dir):
        for file in files:
            if file.endswith(('.md', '.mdx')):
                filepath = os.path.join(root, file)
                chunks = parse_mdx(filepath, base_dir)
                all_chunks.extend(chunks)
                
    print(f"      Created {len(all_chunks)} chunks from docs.")
    return all_chunks

def index_into_qdrant(chunks: List[Dict]):
    """Embeds and indexes chunks into Qdrant."""
    print("[4/5] Initializing Vector DB and Embedding model...")
    client = _get_client()
    model = _get_embed_model()
    
    if not client or not model:
        print("Error: Could not initialize Qdrant or FastEmbed.")
        return

    _init_collection()

    from qdrant_client.models import PointStruct

    print(f"[5/5] Embedding and indexing {len(chunks)} chunks... (this may take a few minutes)")
    
    # Process in batches
    batch_size = 100
    total_indexed = 0
    
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i+batch_size]
        texts = [c["text"] for c in batch]
        
        # Embed
        embeddings = list(model.embed(texts))
        
        points = []
        for j, emb in enumerate(embeddings):
            pt = PointStruct(
                id=str(uuid.uuid4()),
                vector=emb.tolist(),
                payload=batch[j]
            )
            points.append(pt)
            
        client.upsert(
            collection_name=COLLECTION_NAME,
            points=points
        )
        total_indexed += len(points)
        print(f"      Indexed {total_indexed}/{len(chunks)} chunks...")

    print("✅ Ingestion complete! The Vector DB is now ready for RAG.")

def run_ingestion(limit: int = None):
    # به جای دانلود از گیت‌هاب لیارا، از داکیومنت‌های نمونه لوکال استفاده می‌کنیم
    sample_dir = os.path.join(os.path.dirname(__file__), "sample_docs")
    if not os.path.exists(sample_dir):
        print("Sample docs directory not found.")
        return
        
    try:
        chunks = process_directory(sample_dir)
        if limit:
            chunks = chunks[:limit]
            print(f"Limiting to {limit} chunks for testing...")
        if chunks:
            index_into_qdrant(chunks)
        else:
            print("No chunks found. Something went wrong.")
    except Exception as e:
        print(f"Ingestion failed: {e}")

if __name__ == "__main__":
    run_ingestion()

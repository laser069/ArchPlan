import fitz  # PyMuPDF
import os
import asyncio
from sentence_transformers import SentenceTransformer
from app.rag.chroma_client import collection, client

# 🔥 CONFIG
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DOCS_PATH = os.path.join(BASE_DIR, "docs")
CHUNK_SIZE = 1200 
CHUNK_OVERLAP = 300

_model = None

def get_model():
    global _model
    if _model is None:
        print("🧠 Loading SentenceTransformer...")
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model

def chunk_text(text, size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    chunks = []
    for i in range(0, len(text), size - overlap):
        chunks.append(text[i : i + size])
    return chunks

async def read_pdf_async(pdf_name):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _read_pdf_sync, pdf_name)

def _read_pdf_sync(pdf_name):
    path = os.path.join(DOCS_PATH, pdf_name)
    doc_pages = []
    try:
        with fitz.open(path) as doc:
            for page_num, page in enumerate(doc):
                text = page.get_text().strip()
                if text:
                    doc_pages.append({
                        "text": text,
                        "source": pdf_name,
                        "page": page_num + 1
                    })
    except Exception as e:
        print(f"❌ Error reading {pdf_name}: {e}")
    return doc_pages

async def main():
    print("🚀 Starting Incremental PDF ingestion...")
    model = get_model()

    # 1. Identify which files to process
    pdf_files = [f for f in os.listdir(DOCS_PATH) if f.endswith(".pdf")]
    if not pdf_files:
        print("⚠️ No PDFs found in /docs!")
        return

    # 🔥 NEW: Check which files are already in the DB to avoid redundant work
    try:
        existing_metas = collection.get(include=['metadatas'])['metadatas']
        processed_files = set(m['source'] for m in existing_metas) if existing_metas else set()
    except Exception:
        processed_files = set()

    new_files = [f for f in pdf_files if f not in processed_files]
    
    if not new_files:
        print("✅ All PDFs in /docs are already indexed. Nothing to do!")
        print(f"📊 Total chunks in DB: {collection.count()}")
        return

    print(f"📂 Found {len(new_files)} new books to add. Processing...")
    
    tasks = [read_pdf_async(pdf) for pdf in new_files]
    results = await asyncio.gather(*tasks)

    all_chunks = []
    metadatas = []

    for pages in results:
        for page in pages:
            chunks = chunk_text(page["text"])
            for chunk in chunks:
                all_chunks.append(chunk)
                metadatas.append({"source": page["source"], "page": page["page"]})

    # 2. Batch Indexing with UPSERT
    total_chunks = len(all_chunks)
    print(f"🧠 Encoding {total_chunks} new chunks...")
    
    BATCH_SIZE = 128
    loop = asyncio.get_event_loop()

    for i in range(0, total_chunks, BATCH_SIZE):
        batch_end = min(i + BATCH_SIZE, total_chunks)
        batch_chunks = all_chunks[i:batch_end]
        batch_metas = metadatas[i:batch_end]
        
        # Unique IDs: source + index
        batch_ids = [f"{m['source']}_{j}" for j, m in enumerate(batch_metas, i)]

        embeddings = await loop.run_in_executor(None, model.encode, batch_chunks)

        # 🔥 CHANGED: Use upsert instead of add
        collection.upsert(
            documents=batch_chunks,
            embeddings=embeddings.tolist(),
            metadatas=batch_metas,
            ids=batch_ids
        )
        print(f"✅ Indexed {batch_end}/{total_chunks}...")

    print(f"\n✨ Ingestion complete! Total chunks in DB: {collection.count()}")

if __name__ == "__main__":
    asyncio.run(main())
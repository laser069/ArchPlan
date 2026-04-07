import os
from sentence_transformers import SentenceTransformer
from .chroma_client import collection, client,DB_PATH

# 🔥 CONFIG
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DOCS_PATH = os.path.join(BASE_DIR, "docs")
CHUNK_SIZE = 500
CHUNK_OVERLAP = 100

# load embedding model
model = SentenceTransformer("all-MiniLM-L6-v2")

def read_docs():
    docs = []

    for filename in os.listdir(DOCS_PATH):
        if filename.endswith(".txt"):
            path = os.path.join(DOCS_PATH, filename)

            with open(path, "r", encoding="utf-8") as f:
                text = f.read().strip()

                if text:
                    docs.append({
                        "text": text,
                        "source": filename
                    })

    return docs


def chunk_text(text, size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    chunks = []
    # Use a range-based approach for cleaner character slicing
    for i in range(0, len(text), size - overlap):
        chunk = text[i : i + size]
        chunks.append(chunk)
    return chunks

def main():
    print("🚀 Starting ingestion...")

    # 1. Clear existing data
    try:
        # Check if collection has items before deleting to avoid errors
        if collection.count() > 0:
            collection.delete(where={})
            print("🧹 Cleared old data")
    except Exception as e:
        print(f"⚠️ Note: Could not clear collection: {e}")

    # 2. Load and process documents
    docs = read_docs()
    print(f"📂 Loaded {len(docs)} documents")

    all_chunks = []
    metadatas = []

    for doc in docs:
        chunks = chunk_text(doc["text"])
        for chunk in chunks:
            all_chunks.append(chunk)
            metadatas.append({"source": doc["source"]})

    total_chunks = len(all_chunks)
    print(f"✂️ Created {total_chunks} chunks")

    # 3. Process in batches (prevents OOM errors)
    BATCH_SIZE = 128 
    print(f"🧠 Generating embeddings and storing in batches of {BATCH_SIZE}...")

    for i in range(0, total_chunks, BATCH_SIZE):
        batch_end = min(i + BATCH_SIZE, total_chunks)
        
        batch_chunks = all_chunks[i:batch_end]
        batch_metas = metadatas[i:batch_end]
        batch_ids = [f"chunk_{j}" for j in range(i, batch_end)]

        # Generate embeddings for this specific batch
        batch_embeddings = model.encode(batch_chunks).tolist()

        # Add batch to Chroma
        collection.add(
            documents=batch_chunks,
            embeddings=batch_embeddings,
            metadatas=batch_metas,
            ids=batch_ids
        )
        
        print(f"✅ Indexed {batch_end}/{total_chunks} chunks...")

    print("\n✨ Ingestion complete!")
    print(f"📊 Total chunks stored in {DB_PATH}: {collection.count()}")
if __name__ == "__main__":
    main()

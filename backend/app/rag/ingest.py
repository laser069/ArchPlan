import os
from sentence_transformers import SentenceTransformer
from .chroma_client import collection

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


def chunk_text(text):
    chunks = []
    start = 0

    while start < len(text):
        end = start + CHUNK_SIZE
        chunk = text[start:end]

        chunks.append(chunk)

        start += CHUNK_SIZE - CHUNK_OVERLAP

    return chunks



def main():
    print("🚀 Starting ingestion...")

    try:
        collection.delete(where={})
        print("🧹 Cleared old data")
    except:
        pass

    docs = read_docs()
    print(f"📂 Loaded {len(docs)} documents")

    all_chunks = []
    metadatas = []

    for doc in docs:
        chunks = chunk_text(doc["text"])

        for chunk in chunks:
            all_chunks.append(chunk)
            metadatas.append({
                "source": doc["source"]
            })

    print(f"✂️ Created {len(all_chunks)} chunks")

    print("🧠 Generating embeddings...")
    embeddings = model.encode(all_chunks).tolist()

    print("💾 Storing in ChromaDB...")
    collection.add(
        documents=all_chunks,
        embeddings=embeddings,
        metadatas=metadatas,
        ids=[f"chunk_{i}" for i in range(len(all_chunks))]
    )

    print("✅ Ingestion complete!")
    print(f"📊 Total chunks stored: {len(all_chunks)}")


if __name__ == "__main__":
    main()
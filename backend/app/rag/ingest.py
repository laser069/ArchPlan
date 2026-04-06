import os
from sentence_transformers import SentenceTransformer
from rag.chroma_client import collection

model = SentenceTransformer("all-MiniLM-L6-v2")
DOCS_PATH = "../docs" 
def read_docs():
    docs = []
    for filename in os.listdir(DOCS_PATH):
        if filename.endswiths(".txt"):
            with open(os.path.join(DOCS_PATH,filename), 'r',encoding="utf-8") as f:
                text = f.read()
                docs.append(text)
    return docs

def chunk_text(text, chunk_size=500, overlap=100):
    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start += chunk_size - overlap

    return chunks

def main():
    print("📂 Reading docs...")
    docs = read_docs()

    all_chunks = []

    print("✂️ Chunking docs...")
    for doc in docs:
        chunks = chunk_text(doc)
        all_chunks.extend(chunks)

    print(f"Total chunks: {len(all_chunks)}")

    print("🧠 Creating embeddings...")
    embeddings = model.encode(all_chunks).tolist()

    print("💾 Storing in Chroma...")
    collection.add(
        documents=all_chunks,
        embeddings=embeddings,
        ids=[f"doc_{i}" for i in range(len(all_chunks))]
    )

    print("✅ Ingestion complete!")


if __name__ == "__main__":
    main()
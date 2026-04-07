from sentence_transformers import SentenceTransformer
from app.rag.chroma_client import collection

# load embedding model (same as ingest)
model = SentenceTransformer("all-MiniLM-L6-v2")


def retrieve_context(query: str, k: int = 4) -> str:

    #Step 1: convert query → embedding
    query_embedding = model.encode([query]).tolist()

    #Step 2: search in vector DB
    results = collection.query(
        query_embeddings=query_embedding,
        n_results=k
    )

    #Step 3: extract documents
    docs = results.get("documents", [[]])[0]

    #Step 4: combine into context string
    context = "\n\n".join(docs)

    return context
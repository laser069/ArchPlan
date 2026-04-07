from sentence_transformers import SentenceTransformer
from app.rag.chroma_client import collection

model = SentenceTransformer("all-MiniLM-L6-v2")

def get_relevant_docs(query: str, n_results: int = 3):
    # Vectorize the user's specific request
    query_emb = model.encode(query).tolist()
    
    # Query ChromaDB
    results = collection.query(
        query_embeddings=[query_emb],
        n_results=n_results
    )
    
    # Join documents into one string for the prompt
    if results['documents'] and len(results['documents'][0]) > 0:
        return "\n".join(results['documents'][0])
    return None
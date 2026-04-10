from sentence_transformers import SentenceTransformer
from app.rag.chroma_client import collection

_model = None

def _get_model():
    """Lazy-load the embedding model on first use to avoid blocking startup."""
    global _model
    if _model is None:
        print("[INFO] Loading embedding model (first use)...")
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model

def get_relevant_docs(query: str, n_results: int = 3):
    """Query ChromaDB for relevant architectural patterns."""
    model = _get_model()
    query_emb = model.encode(query).tolist()
    
    results = collection.query(
        query_embeddings=[query_emb],
        n_results=n_results
    )
    
    if results['documents'] and len(results['documents'][0]) > 0:
        return "\n".join(results['documents'][0])
    return None
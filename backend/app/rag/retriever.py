from sentence_transformers import SentenceTransformer
from app.rag.chroma_client import collection

_model = None

def _get_model():
    global _model
    if _model is None:
        print("Loading embedding model...")
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model

def get_relevant_docs(query: str, n_results: int = 2) -> str:
    model = _get_model()
    query_emb = model.encode(query).tolist()
    results = collection.query(query_embeddings=[query_emb], n_results=n_results)

    if results['documents'] and len(results['documents'][0]) > 0:
        docs = [
            results['documents'][0][i][:300].strip()
            for i in range(len(results['documents'][0]))
        ]
        return "\n---\n".join(docs)

    return ""

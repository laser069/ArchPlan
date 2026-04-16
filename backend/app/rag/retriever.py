from sentence_transformers import SentenceTransformer
from app.rag.chroma_client import collection

# Initialize a global variable to hold the model
_model = None

def _get_model():
    """Lazy-loads the model only when needed to save memory on startup."""
    global _model
    if _model is None:
        print("🧠 Loading embedding model into memory...")
        # This will use the locally cached model you downloaded during ingestion
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model

def get_relevant_docs(query: str, n_results: int = 3):
    # 1. Get the model using the helper function
    model = _get_model()
    
    # 2. Encode the user query
    query_emb = model.encode(query).tolist()
    
    # 3. Query ChromaDB
    results = collection.query(
        query_embeddings=[query_emb],
        n_results=n_results
    )
    
    formatted_results = []
    
    # 4. Format the output with metadata (Page Numbers)
    if results['documents'] and len(results['documents'][0]) > 0:
        for i in range(len(results['documents'][0])):
            text = results['documents'][0][i]
            # Safely get page metadata
            meta = results['metadatas'][0][i]
            page = meta.get('page', 'Unknown')
            
            formatted_results.append(f"📖 [Page {page}]:\n{text}")
            
        return "\n\n---\n\n".join(formatted_results)
    
    return "⚠️ No relevant information found in the book."
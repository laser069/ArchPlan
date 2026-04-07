from app.rag.retriever import retrieve_context

query = "design a caching system"

context = retrieve_context(query)

print("\n=== RAG CONTEXT ===\n")
print(context)
from app.rag.retriever import retrieve_context

query = "What is bucket token algorithm"

context = retrieve_context(query)

print("\n=== RAG CONTEXT ===\n")
print(context)
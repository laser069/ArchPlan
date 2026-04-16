from app.rag.retriever import get_relevant_docs

def test_my_retriever():
    # These are high-probability topics in the Alex Xu book
    queries = [
        "How to design a rate limiter?",
        # "Explain the token bucket algorithm"
    ]

    print("🚀 Testing Retriever Logic...\n")

    for q in queries:
        print(f"🔍 Testing Query: '{q}'")
        # n_results=2 means we want the top 2 matching pages
        results = get_relevant_docs(q, n_results=2)
        
        if results:
            print(f"✅ FOUND:\n{results}")
        else:
            print("❌ NOTHING FOUND. Did you run the ingestion script successfully?")
        print("-" * 50)

if __name__ == "__main__":
    test_my_retriever()